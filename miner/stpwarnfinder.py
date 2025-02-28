#!/usr/bin/env python3

import argparse
import json
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
    prog="Spotbugs TP warning finder tool", description="Spotbugs TP warning finder tool"
)

parser.add_argument("--local-repo", required=True, nargs=1, type=pathlib.Path)
parser.add_argument("--top-commit", required=True, nargs=1, type=pathlib.Path)
parser.add_argument("--reports", required=True, nargs=1, type=pathlib.Path)
parser.add_argument("--output", required=True, nargs=1, type=pathlib.Path)

args = parser.parse_args()

local_repo = str(args.local_repo[0])
tcfn = str(args.top_commit[0])
reports = str(args.reports[0])
output = str(args.output[0])

if not os.path.exists(local_repo):
    logger.error(f"Local repository {local_repo} does not exist.")
    exit(1)

if not os.path.exists(tcfn):
    logger.error(f"Top commits file {tcfn} does not exist.")
    exit(1)

if not os.path.exists(reports):
    logger.error(f"Spotbugs reports dir {reports} does not exist.")
    exit(1)

repo = Repo(local_repo)

remote_url = repo.remotes.origin.url.split(".git")[0]

with open(tcfn, "r", encoding="utf-8") as tcf:
    top_cmts = json.load(tcf)

warn_db = []

for top_cmt in alive_it(top_cmts, title="Searching for Spotbugs TP warnings", bar="classic"):

    if not top_cmt["parents"]:
        continue

    prnt_cmt = top_cmt["parents"][0]

    diff = repo.git.diff(
        prnt_cmt,
        top_cmt["id"],
        "***.java",
        patch=True,
        unified=0,
        src_prefix="",
        dst_prefix="",
    )

    if not diff:
        continue

    if not os.path.exists(os.path.join(reports, f"report_{top_cmt['id'][:7]}.tar.gz")):
        continue

    with tarfile.open(
        os.path.join(reports, f"report_{top_cmt['id'][:7]}.tar.gz"), "r:gz"
    ) as targz:
        targz.extractall(reports, filter="fully_trusted")

    if not os.path.exists(os.path.join(reports, f"report_{top_cmt['id'][:7]}.xml")):
        continue

    top_report = ET.parse(os.path.join(reports, f"report_{top_cmt['id'][:7]}.xml"))

    top_bugs = top_report.findall("BugInstance")

    if not os.path.exists(os.path.join(reports, f"report_{prnt_cmt[:7]}.tar.gz")):
        continue

    with tarfile.open(
        os.path.join(reports, f"report_{prnt_cmt[:7]}.tar.gz"), "r:gz"
    ) as targz:
        targz.extractall(reports, filter="fully_trusted")

    if not os.path.exists(os.path.join(reports, f"report_{prnt_cmt[:7]}.xml")):
        continue

    prnt_report = ET.parse(os.path.join(reports, f"report_{prnt_cmt[:7]}.xml"))

    parent_bugs = prnt_report.findall("BugInstance")

    if len(parent_bugs) < 1:
        continue

    patch_set = PatchSet(StringIO(diff))

    for parent_bug in parent_bugs:
        parent_bug_details = parent_bug.findall("SourceLine")[0]

        if parent_bug_details is None:
            continue

        if not parent_bug_details.get("sourcepath"):
            continue

        patch_file_of_parent_bug = None
        for patch_file in patch_set:
            if patch_file.source_file.endswith(parent_bug_details.get("sourcepath")):
                patch_file_of_parent_bug = patch_file
                break

        if not patch_file_of_parent_bug:
            continue

        if not parent_bug_details.get("start") or not parent_bug_details.get("end"):
            continue

        AFFECTED = False
        for hunk in patch_file_of_parent_bug:
            src_start = hunk.source_start
            src_end = src_start + hunk.source_length - 1
            if src_start <= int(parent_bug_details.get("start")) and int(parent_bug_details.get("end")) <= src_end:
                AFFECTED = True

        if not AFFECTED:
            continue

        FIX = True
        for top_bug in top_bugs:

            if top_bug.get("type") != parent_bug.get("type"):
                continue

            top_bug_details = top_bug.findall("SourceLine")[0]

            if top_bug_details is None:
                continue

            if not top_bug_details.get("sourcepath"):
                continue

            patch_file_of_top_bug = None
            for patch_file in patch_set:
                if patch_file.target_file.endswith(top_bug_details.get("sourcepath")):
                    patch_file_of_top_bug = patch_file
                    break

            if not patch_file_of_top_bug:
                continue

            if not top_bug_details.get("start") or not top_bug_details.get(
                    "end"):
                continue

            for hunk in patch_file_of_top_bug:
                target_start = hunk.target_start
                target_end = target_start + hunk.target_length - 1
                if target_start <= int(top_bug_details.get("start")) and int(top_bug_details.get(
                        "end")) <= target_end:
                    FIX = False
                    break

        if FIX:
            warn_db.append(create_warn(tool="Spotbugs", repo_url=remote_url, commit_sha=prnt_cmt,
                                       commit_date=get_iso_commit_date(repo.commit(prnt_cmt)),
                                       violation=parent_bug,
                                       filepath=patch_file_of_parent_bug.source_file, label=1))
            
    os.remove(os.path.join(reports, f"report_{top_cmt['id'][:7]}.xml"))
    os.remove(os.path.join(reports, f"report_{prnt_cmt[:7]}.xml"))

logger.info(f"Found {len(warn_db)} Spotbugs TP warning{'s' if len(warn_db) > 1 else ''}.")
if len(warn_db) < 1:
    logger.warning("No output was generated by Spotbugs TP warning finder.")
    exit()

tp_warn_db = pd.DataFrame.from_records(warn_db)
tp_warn_db.to_csv(output, encoding='utf-8', index=False)
