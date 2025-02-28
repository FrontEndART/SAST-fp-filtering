#!/usr/bin/env python3

import argparse
import datetime
import json
import os
import shutil
import subprocess
import sys
import tarfile

import docker
from alive_progress import alive_it
from git import Repo
from loguru import logger

from GitRemoteProgress import GitRemoteProgress
from Project import Project

logger.remove(0)
logger.add(sys.stderr, format="<green>{time:YYYY.MM.DD. HH:mm:ss}</green> <bold>[{level}]</bold>: {message}",
           colorize=True)

TIMESTAMP = datetime.datetime.now().timestamp()

BASE_PATH = os.path.dirname(os.path.abspath(__file__))

WARN_DB = os.path.join(BASE_PATH, "warn_db")

DIFFGITJAVA = os.path.join(BASE_PATH, "diffgitjava.py")
TOPCOM = os.path.join(BASE_PATH, "topcom.py")
PGENREP = os.path.join(BASE_PATH, "pgenrep.py")
SGENREP = os.path.join(BASE_PATH, "sgenrep.py")
RULESET = os.path.join(BASE_PATH, "ruleset.xml")
PTPWARNFINDER = os.path.join(BASE_PATH, "ptpwarnfinder.py")
PFPWARNFINDER = os.path.join(BASE_PATH, "pfpwarnfinder.py")
STPWARNFINDER = os.path.join(BASE_PATH, "stpwarnfinder.py")
SFPWARNFINDER = os.path.join(BASE_PATH, "sfpwarnfinder.py")
CADET = os.path.join(BASE_PATH, "cadet.py")
SKIP = os.path.join(BASE_PATH, "skip.py")

IMG_NAME = "vfdetector-extended"

DOCKER_BASE_PATH = "/VFDetector"

DFLT_ENC = "utf-8"

PMD = "pmd"
SPOTBUGS = "spotbugs"

parser = argparse.ArgumentParser(prog="miner", description="A miner to collect warnings from real-life projects")

parser.add_argument("--repo-url", required=True, nargs=1)
parser.add_argument("--limit", required=False, nargs="?", type=int)
parser.add_argument("--chunk-size", required=False, nargs="?", type=int)
parser.add_argument("--shm-size", required=False, nargs="?", type=str, default="16g")
parser.add_argument(
    "--since", required=False, nargs="?", type=datetime.date.fromisoformat
)
parser.add_argument(
    "--until", required=False, nargs="?", type=datetime.date.fromisoformat
)
parser.add_argument("--pmd", required=False, action="store_true")
parser.add_argument("--spotbugs", required=False, action="store_true")
parser.add_argument("--only-commit-data", required=False, action="store_true")

args = parser.parse_args()

repo_url = args.repo_url[0]

limit = args.limit if "limit" in args else None
chunk_size = args.chunk_size if "chunk-size" in args else None
shm_size = args.shm_size
since = args.since if "since" in args else None
until = args.until if "until" in args else None


def clean_up(tmp_dir, do_exit=True, exit_code=1):
    print(f"Removing dir {tmp_dir}...", end="")
    shutil.rmtree(tmp_dir)
    print("Done.")
    if do_exit:
        exit(exit_code)

def create_dataset(project, sca):
    if not os.listdir(project.get_warn_db_dir()):
        return

    if not os.path.exists(project.get_dataset_dir()):
        os.makedirs(project.get_dataset_dir())

    cadet_out = subprocess.run([
        CADET,
        "--local-repo",
        project.get_local_repo(),
        "--warn-db-dir",
        project.get_warn_db_dir(),
        "--dataset-dir",
        project.get_dataset_dir(),
        "--sca",
        sca
    ])

    if cadet_out.returncode:
        logger.error("Failed to create dataset.")


project = Project(
    repo_url=repo_url,
    tmp_dir="",
    warn_db=WARN_DB,
)

logger.info(f"Started to process project {project.get_name()}.")

TMP_DIR = os.path.join(BASE_PATH, f"tmp_{project.get_name().replace('-','_')}")
project.tmp_dir = TMP_DIR

if not os.path.exists(project.get_warn_db_dir()):
    os.makedirs(project.get_warn_db_dir())

print("Creating dir for temp files...", end="")
if not os.path.exists(TMP_DIR):
    os.mkdir(TMP_DIR)
print("Done.")
logger.info(f"temp dir path: {TMP_DIR}")

print("Creating dir for warning database...", end="")
if not os.path.exists(WARN_DB):
    os.mkdir(WARN_DB)
print("Done.")

if not os.path.exists(project.get_local_repo()):
    print("Cloning repository...")
    Repo.clone_from(
        url=project.repo_url,
        to_path=project.get_local_repo(),
        progress=GitRemoteProgress(),
    )
    print("End of cloning repository.")

os.makedirs(project.get_code_chg_dir())

diffgitjava_cmd = [
    DIFFGITJAVA,
    "--local-repository",
    project.get_local_repo(),
    "--output-dir",
    project.get_code_chg_dir(),
]

if since:
    diffgitjava_cmd.extend(["--since", str(since)])

if until:
    diffgitjava_cmd.extend(["--until", str(until)])

if chunk_size:
    diffgitjava_cmd.extend(["--chunk-size", chunk_size])

diffgitjava_out = subprocess.run(diffgitjava_cmd)

if diffgitjava_out.returncode:
    logger.error(f"Searching is failed. End of processing {project.get_name()}.")
    clean_up(TMP_DIR)

if not os.listdir(project.get_code_chg_dir()):
    logger.info(f"No relevant code change was detected. End of processing {project.get_name()}.")
    clean_up(TMP_DIR)

if args.only_commit_data:
    clean_up(TMP_DIR,exit_code=0)

if not os.path.exists(project.get_top_cmt_dir()):
    os.makedirs(project.get_top_cmt_dir())

if limit:
    print("Building docker image...", end="")
    client = docker.from_env()


    client.images.build(path=BASE_PATH, tag=IMG_NAME)
    print("Done.")

    CONT_NAME = f"vfdetector-container-{project.get_name()}"

    print("Starting docker container...", end="")
    docker_container = client.containers.run(
        image=IMG_NAME,
        name=CONT_NAME,
        stdin_open=True,
        tty=True,
        detach=True,
        shm_size=shm_size,
    )
    print("Done.")
    logger.info(f"docker container name: {CONT_NAME}")

    print("Creating dir in container...", end="")
    docker_container.exec_run(["mkdir", "-p" "/VFDetector/cmt_rank"])
    print("Done.")

    print("Copying diff data to container...", end="")

    CODE_CHG = os.path.join(TMP_DIR, "code_chg.tar")

    with tarfile.open(CODE_CHG, "w") as tar:
        tar.add(project.get_code_chg_dir(), arcname="code_chg")

    with open(CODE_CHG, "rb") as data:
        docker_container.put_archive(
            "/VFDetector",
            data=data,
        )

    os.remove(CODE_CHG)
    print("Done.")


    docker_container.exec_run(
        [
            "mkdir",
            "-p",
            os.path.join(
                "/VFDetector/cmt_rank",
            ),
        ]
    )

    code_change_files = os.listdir(project.get_code_chg_dir())

    for code_change_file in alive_it(code_change_files, title="Ranking commits", bar="classic"):
        commit_result_file = code_change_file.replace("code_change", "commit_ranking")

        (exit_code, output) = docker_container.exec_run(
            cmd=[
                "python3",
                "application.py",
                "-mode",
                "ranking",
                "-input",
                os.path.join("code_chg", code_change_file),
                "-output",
                os.path.join("cmt_rank", commit_result_file),
            ],
            workdir=DOCKER_BASE_PATH,
        )

    if not os.path.exists(project.get_cmt_rank_dir()):
        os.makedirs(project.get_cmt_rank_dir())

    # Copy the results from the docker container to host
    print("Copying commit rankings to host...", end="")
    bits, stat = docker_container.get_archive(
        os.path.join(
            DOCKER_BASE_PATH,
            "cmt_rank"
        )
    )

    CMT_RNK = os.path.join(TMP_DIR, "cmt_rank.tar")

    with open(CMT_RNK, "wb") as data:
        for chunk in bits:
            data.write(chunk)

    with tarfile.open(CMT_RNK, "r") as tar:
        tar.extractall(TMP_DIR, filter="fully_trusted")

    os.remove(CMT_RNK)
    print("Done.")

    print("Merging commit rankings into a single file...", end="")
    commit_result_chunks = os.listdir(project.get_cmt_rank_dir())

    commit_result = []
    for commit_result_chunk in commit_result_chunks:
        with open(
                os.path.join(
                    project.get_cmt_rank_dir(),
                    commit_result_chunk,
                ),
                "r",
                encoding=DFLT_ENC,
        ) as o:
            commit_result.extend(json.load(o))

    commit_result.sort(key=lambda x: x["score"], reverse=True)

    with open(
            project.get_cmt_rank(),
            "w",
            encoding=DFLT_ENC,
    ) as f:
        json.dump(commit_result, f)
    print("Done.")

    print("Stopping container...", end="")
    docker_container.stop()
    print("Done.")

    print("Removing container...", end="")
    docker_container.remove()
    print("Done.")

    #os.makedirs(project.get_top_cmt_dir())

    print("Selecting top commits...", end="")
    topcom_command = [
        TOPCOM,
        "--commit-rank",
        project.get_cmt_rank(),
        "--local-repo",
        project.get_local_repo(),
        "--output",
        project.get_top_cmt(),
    ]

    topcom_command.extend(["--limit", str(limit)])

    topcom_out = subprocess.run(
        topcom_command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    if topcom_out.returncode:
        logger.error(f"Failed to select top commits. End of processing {project.get_name()}.")
        clean_up(TMP_DIR)
    print("Done.")

else:
    skip_command = subprocess.run([
        SKIP,
        "--local-repo",
        project.get_local_repo(),
        "--code-change-dir",
        project.get_code_chg_dir(),
        "--output",
        project.get_top_cmt(),
    ])

    if skip_command.returncode:
        logger.error(f"Failed to select commits. End of processing {project.get_name()}.")
        clean_up(TMP_DIR)


if args.pmd:

    os.makedirs(project.get_sca_report_dir(tool=PMD))

    pgenrep_cmd = [
        PGENREP,
        "--local-repo",
        project.get_local_repo(),
        "--ruleset-file",
        RULESET,
        "--output-dir",
        project.get_sca_report_dir(tool=PMD),
    ]

    if since:
        pgenrep_cmd.extend(["--since", str(since)])

    if until:
        pgenrep_cmd.extend(["--until", str(until)])

    pgenrep_out = subprocess.run(pgenrep_cmd)

    if pgenrep_out.returncode:
        logger.error("Failed to generate PMD reports.")


    ptpwarnfinder_out = subprocess.run(
        [
            PTPWARNFINDER,
            "--local-repo",
            project.get_local_repo(),
            "--top-commit",
            project.get_top_cmt(),
            "--reports",
            project.get_sca_report_dir(tool=PMD),
            "--output",
            project.get_tp_warn_db(tool=PMD),
        ]
    )

    if ptpwarnfinder_out.returncode:
        logger.error("Failed to find PMD TP warnings.")

    pfpwarnfinder_cmd = [
        PFPWARNFINDER,
        "--local-repo",
        project.get_local_repo(),
        "--tp-warn-db",
        project.get_tp_warn_db(tool=PMD),
        "--reports",
        project.get_sca_report_dir(tool=PMD),
        "--output",
        project.get_fp_warn_db(tool=PMD)
    ]

    if since:
        pfpwarnfinder_cmd.extend(["--since", str(since)])

    if until:
        pfpwarnfinder_cmd.extend(["--until", str(until)])

    pfpwarnfinder_out = subprocess.run(pfpwarnfinder_cmd)

    if pfpwarnfinder_out.returncode:
        logger.error("Failed to find PMD FP warnings.")

    clean_up(project.get_sca_report_dir(tool=PMD), do_exit=False)

    create_dataset(project=project, sca=PMD)

if args.spotbugs:

    os.makedirs(project.get_deps_dir())

    os.makedirs(project.get_sca_report_dir(tool=SPOTBUGS))

    sgenrep_cmd = [
        SGENREP,
        "--local-repo",
        project.get_local_repo(),
        "--dependency-dir",
        project.get_deps_dir(),
        "--output-dir",
        project.get_sca_report_dir(tool=SPOTBUGS),
    ]

    if since:
        sgenrep_cmd.extend(["--since", str(since)])

    if until:
        sgenrep_cmd.extend(["--until", str(until)])

    sgenrep_out = subprocess.run(sgenrep_cmd)

    if sgenrep_out.returncode:
        logger.error("Failed to generate Spotbugs reports.")


    stpwarnfinder_out = subprocess.run(
        [
            STPWARNFINDER,
            "--local-repo",
            project.get_local_repo(),
            "--top-commit",
            project.get_top_cmt(),
            "--reports",
            project.get_sca_report_dir(tool=SPOTBUGS),
            "--output",
            project.get_tp_warn_db(tool=SPOTBUGS),
        ]
    )

    if stpwarnfinder_out.returncode:
        logger.error("Failed to find Spotbugs TP warnings.")

    sfpwarnfinder_cmd = [
        SFPWARNFINDER,
        "--local-repo",
        project.get_local_repo(),
        "--tp-warn-db",
        project.get_tp_warn_db(tool=SPOTBUGS),
        "--reports",
        project.get_sca_report_dir(tool=SPOTBUGS),
        "--output",
        project.get_fp_warn_db(tool=SPOTBUGS)
    ]

    if since:
        sfpwarnfinder_cmd.extend(["--since", str(since)])

    if until:
        sfpwarnfinder_cmd.extend(["--until", str(until)])

    sfpwarnfinder_out = subprocess.run(sfpwarnfinder_cmd)

    if sfpwarnfinder_out.returncode:
        logger.error("Failed to find Spotbugs FP warnings.")

    clean_up(project.get_sca_report_dir(tool=SPOTBUGS), do_exit=False)

    create_dataset(project=project, sca=SPOTBUGS)


logger.info(f"End of processing project {project.get_name()}.")
clean_up(TMP_DIR,exit_code=0)
