#!/usr/bin/env python3

import argparse
import os
import subprocess
import shutil
import json
import sys
import datetime
import docker
import tarfile

import MinerPath

from alive_progress import alive_it

from pathlib import Path

from git import Repo

from GitRemoteProgress import GitRemoteProgress

from Project import Project


BASE_PATH = os.path.dirname(os.path.abspath(__file__))
TMP_DIR = os.path.join(BASE_PATH, "tmp")
WARN_DB = os.path.join(BASE_PATH, "warn_db")

DIFFGITJAVA = os.path.join(BASE_PATH, "diffgitjava.py")
TOPCOM = os.path.join(BASE_PATH, "topcom.py")
GENREP = os.path.join(BASE_PATH, "genrep.py")
RULESET = os.path.join(BASE_PATH, "ruleset.xml")
WARNFINDER = os.path.join(BASE_PATH, "warnfinder2.py")

CODE_CHG = os.path.join(TMP_DIR, "code_chg.tar")
CMT_RNK = os.path.join(TMP_DIR, "cmt_rank.tar")


IMG_NAME = "vfdetector-extended"
CONT_NAME = "vfdetector-container"


DFLT_ENC = "utf-8"


parser = argparse.ArgumentParser(prog="pipeline", description="Pipeline for VFDetector")

parser.add_argument("--repo-list", required=True, nargs=1, type=Path)
parser.add_argument("--shm-size", required=True, nargs=1)
parser.add_argument("--limit", required=False, nargs="?", type=int)
parser.add_argument("--chunk-size", required=False, nargs="?", type=int)
parser.add_argument(
    "--since", required=False, nargs="?", type=datetime.date.fromisoformat
)
parser.add_argument(
    "--until", required=False, nargs="?", type=datetime.date.fromisoformat
)


# Parse command line arguments
args = parser.parse_args()

repo_list = args.repo_list[0]
shm_size = args.shm_size[0]

limit = args.limit if "limit" in args else None
chunk_size = args.chunk_size if "chunk-size" in args else None
since = args.since if "since" in args else None
until = args.until if "until" in args else None
clean_tmp = "clean-tmp" in args


# Read the list of repositories to be analyzed
if not os.path.exists(repo_list):
    print(
        f"[ERROR]: Repository list file {repo_list} does not exist. Exited.",
        file=sys.stderr,
    )
    exit(1)

print("Parsing repo URL(s)...", end="")
with open(repo_list, "r", encoding=DFLT_ENC) as i:
    repo_urls = i.read().strip().splitlines()
print("Done.")

# Create dir for temporary files
print("Creating dir for temp files...", end="")
if not os.path.exists(TMP_DIR):
    os.mkdir(TMP_DIR)
print("Done.")


# Create dir for warning database
print("Creating dir for warning database...", end="")
if not os.path.exists(WARN_DB):
    os.mkdir(WARN_DB)
print("Done.")

client = docker.from_env()

print("Building docker image for VFDetector...", end="")
client.images.build(path=BASE_PATH, tag=IMG_NAME)
print("Done.")

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

print("Creating dirs in container...", end="")
docker_container.exec_run(["mkdir", "-p", "/VFDetector/code_chg"])
docker_container.exec_run(["mkdir", "-p" "/VFDetector/cmt_rank"])
print("Done.")

for repo_url in repo_urls:

    project = Project(
        repo_url=repo_url,
        tmp_dir=TMP_DIR,
        warn_db=WARN_DB,
    )

    print("Cloning repository...")
    Repo.clone_from(
        url=project.repo_url,
        to_path=project.get_local_repo(),
        progress=GitRemoteProgress(),
    )
    print("End of cloning repository.")

    print("Searching for relevant code changes...")
    os.makedirs(project.get_code_chg_dir())

    command = [
        DIFFGITJAVA,
        "--local-repository",
        project.get_local_repo(),
        "--output-dir",
        project.get_code_chg_dir(),
    ]

    if since:
        command.extend(["--since", str(since)])

    if until:
        command.extend(["--until", str(until)])

    if chunk_size:
        command.extend(["--chunk-size", chunk_size])

    diffgitjava_out = subprocess.run(command)

    if diffgitjava_out.returncode:
        print(f"Searching is failed. End of processing {project.get_name()}.")
        continue

    print("End of searching.")

    if not os.listdir(project.get_code_chg_dir()):
        print(
            f"No relevant code change was detected. End of processing {project.get_name()}."
        )
        continue

    print("Copying code changes to container...", end="")

    with tarfile.open(CODE_CHG, "w") as tar:
        tar.add(project.get_code_chg_dir(), arcname=project.get_name())

    with open(CODE_CHG, "rb") as data:
        docker_container.put_archive(
            "/VFDetector/code_chg",
            data=data,
        )

    os.remove(CODE_CHG)
    print("Done.")

    print("Running VFDetector...")
    if not os.path.exists(project.get_cmt_rank_dir()):
        os.makedirs(project.get_cmt_rank_dir())

    docker_container.exec_run(
        [
            "mkdir",
            "-p",
            os.path.join(
                "/VFDetector/cmt_rank",
                project.get_name(),
            ),
        ]
    )

    code_change_files = os.listdir(project.get_code_chg_dir())

    for code_change_file in alive_it(code_change_files, bar="classic"):

        commit_result_file = code_change_file.replace("code_change", "commit_ranking")

        (exit_code, output) = docker_container.exec_run(
            cmd=[
                "python3",
                "application.py",
                "-mode",
                "ranking",
                "-input",
                os.path.join("code_chg", project.get_name(), code_change_file),
                "-output",
                os.path.join("cmt_rank", project.get_name(), commit_result_file),
            ],
            workdir=MinerPath.VFDETECTOR_DOCKER_DIR,
        )

    print("End of running VFDetector.")

    # Copy the results from the docker container to host
    print("Copying commit rankings to host...", end="")
    bits, stat = docker_container.get_archive(
        os.path.join(
            MinerPath.VFDETECTOR_DOCKER_DIR,
            "cmt_rank",
            project.get_name(),
        )
    )

    with open(CMT_RNK, "wb") as data:
        for chunk in bits:
            data.write(chunk)

    with tarfile.open(CMT_RNK, "r") as tar:
        tar.extractall(os.path.join(MinerPath.TEMP_DIR_PATH, "cmt_rank"))

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

    os.makedirs(project.get_top_cmt_dir())

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

    if limit:
        topcom_command.extend(["--limit", str(limit)])

    topcom_out = subprocess.run(
        topcom_command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    if topcom_out.returncode:
        print(f"Failed to select top commits. End of processing {project.get_name()}.")
        continue
    print("Done.")

    print("Running PMD on top commits...")
    os.makedirs(project.get_pmd_report_dir())

    os.chdir(project.get_local_repo())
    genrep_out = subprocess.run(
        [
            GENREP,
            "--local-repo",
            ".",
            "--commit-file",
            project.get_top_cmt(),
            "--ruleset-file",
            RULESET,
            "--output-dir",
            project.get_pmd_report_dir(),
        ]
    )

    if genrep_out.returncode:
        print(
            f"Failed to generate PMD reports. End of processing {project.get_name()}."
        )
        continue

    os.chdir(BASE_PATH)
    print("End of running PMD.")

    print("Searching for true positive warnings...")
    if not os.path.exists(project.get_warn_db_dir()):
        os.makedirs(project.get_warn_db_dir())
    warnfinder_out = subprocess.run(
        [
            WARNFINDER,
            "--local-repo",
            project.get_local_repo(),
            "--top-commit",
            project.get_top_cmt(),
            "--reports",
            project.get_pmd_report_dir(),
            "--output",
            project.get_warn_db(),
        ]
    )

    if warnfinder_out.returncode:
        print("Failed to find true positive warnings.")
    else:
        print("End of searching.")

    print(f"End of processing project {project.get_name()}")


print("Stopping container...", end="")
docker_container.stop()
print("Done.")

print("Removing container...", end="")
docker_container.remove()
print("Done.")

print("Removing tmp dir...", end="")
shutil.rmtree(TMP_DIR)
print("Done.")
