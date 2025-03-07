#!/usr/bin/env python3

import argparse
import datetime
import glob
import os
import pathlib
import sys
import tarfile
import xml.etree.ElementTree as ET
from io import StringIO

import pandas as pd
from alive_progress import alive_it
from git import Repo
from loguru import logger
from unidiff import PatchSet

from Transformations import create_warn, get_iso_commit_date

logger.remove(0)
logger.add(sys.stderr, format="<green>{time:YYYY.MM.DD. HH:mm:ss}</green> <bold>[{level}]</bold>: {message}",
           colorize=True)

parser = argparse.ArgumentParser(
    prog="Spotbugs FP warning finder tool", description="Spotbugs FP warning finder tool"
)

parser.add_argument("--local-repo", required=True, nargs=1, type=pathlib.Path)
parser.add_argument("--tp-warn-db", required=True, nargs=1, type=pathlib.Path)
parser.add_argument("--reports", required=True, nargs=1, type=pathlib.Path)
parser.add_argument(
    "--output", required=True, nargs=1, type=pathlib.Path
)
parser.add_argument(
    "--since", required=False, nargs="?", type=datetime.date.fromisoformat
)
parser.add_argument(
    "--until", required=False, nargs="?", type=datetime.date.fromisoformat
)

args = parser.parse_args()

local_repo = str(args.local_repo[0])
tp_warn_db = str(args.tp_warn_db[0])
reports = str(args.reports[0])
output = str(args.output[0])
since = args.since if "since" in args else None
until = args.until if "until" in args else None

if not os.path.exists(local_repo):
    logger.error(f"Local repository {local_repo} does not exist.")
    exit(1)


if not os.path.exists(reports):
    logger.error(f"Spotbugs reports dir {reports} does not exist.")
    exit(1)

repo = Repo(local_repo)

remote_url = repo.remotes.origin.url.split(".git")[0]

commits = list(
    repo.iter_commits(repo.head.name, reverse=True, since=since, until=until)
)

if len(commits) < 2:
    logger.warning(
        "There are no Spotbugs false positive warnings. No output was generated by Spotbugs FP warning finder.")
    exit()

last_commit = commits[-1]

if os.path.exists(tp_warn_db):
    tp_warns = pd.read_csv(tp_warn_db)
    tp_warn_msgs = set(tp_warns["warning_msg"])
else:
    tp_warn_msgs = set()


warn_db = []

os.chdir(local_repo)

for commit in alive_it(commits, title="Searching for Spotbugs FP warnings", bar="classic"):
    if not commit.parents:
        continue

    parent = commit.parents[0]

    repo.git.checkout(parent.hexsha)
    src_files = glob.glob("**/*.java", recursive=True)
    repo.git.checkout(last_commit.hexsha)

    changed_files = repo.git.diff(
        parent.hexsha,
        commit.hexsha,
        "***.java",
        name_only=True
    ).strip().splitlines()

    if not changed_files:
        continue

    diff = repo.git.diff(
        parent.hexsha,
        commit.hexsha,
        "***.java",
        patch=True,
        unified=0,
        src_prefix="",
        dst_prefix="",
    )

    patch_set = PatchSet(StringIO(diff))

    if not os.path.exists(os.path.join(reports, f"report_{parent.hexsha[:7]}.tar.gz")):
        continue

    with tarfile.open(
        os.path.join(reports, f"report_{parent.hexsha[:7]}.tar.gz"), "r:gz"
    ) as targz:
        targz.extractall(reports, filter="fully_trusted")

    if not os.path.exists(os.path.join(reports, f"report_{parent.hexsha[:7]}.xml")):
        continue

    parent_report = ET.parse(os.path.join(reports, f"report_{parent.hexsha[:7]}.xml"))

    parent_bugs = parent_report.findall("BugInstance")

    if not parent_bugs:
        continue

    if not os.path.exists(os.path.join(reports, f"report_{commit.hexsha[:7]}.tar.gz")):
        continue

    with tarfile.open(
        os.path.join(reports, f"report_{commit.hexsha[:7]}.tar.gz"), "r:gz"
    ) as targz:
        targz.extractall(reports, filter="fully_trusted")

    if not os.path.exists(os.path.join(reports, f"report_{commit.hexsha[:7]}.xml")):
        continue

    report = ET.parse(os.path.join(reports, f"report_{commit.hexsha[:7]}.xml"))

    bugs = report.findall("BugInstance")

    if not bugs:
        continue

    for parent_bug in parent_bugs:
        parent_bug_details = parent_bug.findall("SourceLine")[0]
        
        if not parent_bug_details.get("sourcepath"):
            continue

        CHANGED = False
        for changed_file in changed_files:
            if changed_file.endswith(parent_bug_details.get("sourcepath")):
                CHANGED = True
                break
        if not CHANGED:
            AUX_FILE = True
            for src_file in src_files:
                if src_file.endswith(parent_bug_details.get("sourcepath")):
                    source_file = src_file
                    AUX_FILE = False

            if AUX_FILE:
                continue

            warn_db.append(
                create_warn(tool="Spotbugs", repo_url=remote_url, commit_sha=parent.hexsha,
                            commit_date=get_iso_commit_date(parent), violation=parent_bug,
                            filepath=source_file, label=0))
        else:
            target_file = None
            for patch_file in patch_set:
                if patch_file.source_file.endswith(parent_bug_details.get("sourcepath")):
                    source_file = patch_file.source_file
                    target_file = patch_file.target_file
                    break

            if not target_file:
                continue

            for bug in bugs:

                if bug.get("type") != parent_bug.get("type"):
                    continue

                if bug.findall("LongMessage")[0].text != parent_bug.findall("LongMessage")[0].text:
                    continue

                bug_details = bug.findall("SourceLine")[0]
                
                if not bug_details.get("sourcepath"):
                    continue

                if not target_file.endswith(bug_details.get("sourcepath")):
                    continue

                warn_db.append(
                    create_warn(tool="Spotbugs", repo_url=remote_url, commit_sha=parent,
                                commit_date=get_iso_commit_date(parent), violation=parent_bug,
                                filepath=source_file, label=0))
    
    os.remove(os.path.join(reports, f"report_{parent.hexsha[:7]}.xml"))
    os.remove(os.path.join(reports, f"report_{commit.hexsha[:7]}.xml"))

df = pd.DataFrame.from_records(warn_db)
col_names = list(df.columns)
if "warning_type" in col_names and "warning_msg" in col_names and "filename" in col_names:
    df = df.drop_duplicates(subset=["warning_type", "warning_msg", "filename"], keep="last")
if "warning_msg" in col_names:
    df = df[~df["warning_msg"].isin(tp_warn_msgs)]
logger.info(f"Found {len(df)} Spotbugs FP warning{'s' if len(df) > 1 else ''}.")
if len(df) < 1:
    logger.warning("No output was generated by Spotbugs FP warning finder.")
    exit()

df.to_csv(output, encoding='utf-8', index=False)
os.chdir(os.path.dirname(os.path.abspath(__file__)))
