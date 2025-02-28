#!/usr/bin/env python3

import argparse
import json
import os
import pathlib
import sys
import tarfile
from difflib import SequenceMatcher
from io import StringIO

import pandas as pd
from alive_progress import alive_it
from git import Repo
from loguru import logger
from unidiff import PatchSet


from Transformations import create_warn, report_to_dict, get_iso_commit_date

logger.remove(0)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY.MM.DD. HH:mm:ss}</green> <bold>[{level}]</bold>: {message}",
    colorize=True,
)

parser = argparse.ArgumentParser(
    prog="PMD TP warning finder tool", description="PMD TP warning finder tool"
)

parser.add_argument("--local-repo", required=True, nargs=1, type=pathlib.Path)
parser.add_argument("--top-commit", required=True, nargs=1, type=pathlib.Path)
parser.add_argument("--reports", required=True, nargs=1, type=pathlib.Path)
parser.add_argument(
    "--output", required=False, default="./warnings.csv", nargs="?", type=pathlib.Path
)

args = parser.parse_args()

local_repo = str(args.local_repo[0])
tcfn = str(args.top_commit[0])
reports = str(args.reports[0])
output = str(args.output)

if not os.path.exists(local_repo):
    logger.error(f"Local repository {local_repo} does not exist.")
    exit(1)

if not os.path.exists(tcfn):
    logger.error(f"Top commits file {tcfn} does not exist.")
    exit(1)

if not os.path.exists(reports):
    logger.error(f"PMD reports dir {reports} does not exist.")
    exit(1)

repo = Repo(local_repo)

remote_url = repo.remotes.origin.url.split(".git")[0]

with open(tcfn, "r", encoding="utf-8") as tcf:
    top_cmts = json.load(tcf)

warn_db = []

for top_cmt in alive_it(top_cmts, title="Searching for PMD TP warnings", bar="classic"):

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

    if not os.path.exists(os.path.join(reports, f"report_{top_cmt['id'][:7]}.json")):
        continue

    top_violations = report_to_dict(
        os.path.join(reports, f"report_{top_cmt['id'][:7]}.json")
    )

    if not os.path.exists(os.path.join(reports, f"report_{prnt_cmt[:7]}.tar.gz")):
        continue

    with tarfile.open(
        os.path.join(reports, f"report_{prnt_cmt[:7]}.tar.gz"), "r:gz"
    ) as targz:
        targz.extractall(reports, filter="fully_trusted")

    if not os.path.exists(os.path.join(reports, f"report_{prnt_cmt[:7]}.json")):
        continue

    prnt_violations = report_to_dict(
        os.path.join(reports, f"report_{prnt_cmt[:7]}.json")
    )

    if not prnt_violations:
        continue

    patch_set = PatchSet(StringIO(diff))

    for patch_file in patch_set:
        if patch_file.source_file not in prnt_violations:
            continue
        src_violations = prnt_violations[patch_file.source_file]

        for hunk in patch_file:
            src_start = hunk.source_start
            src_end = src_start + hunk.source_length - 1
            for src_violation in src_violations:
                if (
                    src_start <= src_violation["beginline"]
                    and src_violation["endline"] <= src_end
                ):
                    fix = True
                    for other_patch_file in patch_set:
                        if other_patch_file.target_file not in top_violations:
                            continue
                        dst_violations = top_violations[other_patch_file.target_file]
                        for other_hunk in other_patch_file:
                            dst_start = other_hunk.target_start
                            dst_end = dst_start + other_hunk.target_length - 1
                            for dst_violation in dst_violations:
                                if (
                                    dst_start <= dst_violation["beginline"]
                                    and dst_violation["endline"] <= dst_end
                                    and SequenceMatcher(
                                        None,
                                        src_violation["description"],
                                        dst_violation["description"],
                                    ).ratio()
                                    >= 0.75
                                ):
                                    fix = False
                    if fix:
                        warn_db.append(
                            create_warn(
                                tool="PMD",
                                repo_url=remote_url,
                                commit_sha=prnt_cmt,
                                commit_date=get_iso_commit_date(repo.commit(prnt_cmt)),
                                filepath=patch_file.source_file,
                                violation=src_violation,
                                label=1,
                            )
                        )

    os.remove(os.path.join(reports, f"report_{top_cmt['id'][:7]}.json"))
    os.remove(os.path.join(reports, f"report_{prnt_cmt[:7]}.json"))

logger.info(f"Found {len(warn_db)} PMD TP warning{'s' if len(warn_db) > 1 else ''}.")
if len(warn_db) < 1:
    logger.warning("No output was generated by PMD TP warning finder.")
    exit()

tp_warn_db = pd.DataFrame.from_records(warn_db)
tp_warn_db.to_csv(output, encoding="utf-8", index=False)
