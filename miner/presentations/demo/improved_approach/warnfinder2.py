#!/usr/bin/python3

import argparse
import csv
import json
import os
import sys
import pathlib

from git import Repo

from alive_progress import alive_it

from io import StringIO
from unidiff import PatchSet
from deepdiff import DeepDiff, parse_path


HEADERS = [
    "tool",
    "warning_type",
    "warning_msg",
    "commit_sha",
    "repo",
    "filename",
    "positions",
    "label",
]


parser = argparse.ArgumentParser(
    prog="PMD warning finder tool", description="PMD warning finder tool"
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
    print(f"[ERROR]: Local repository {local_repo} does not exist.", file=sys.stderr)
    exit(1)


if not os.path.exists(tcfn):
    print(f"Top commits file {tcfn} does not exist.", file=sys.stderr)
    exit(1)


if not os.path.exists(reports):
    print(f"PMD reports dir {reports} does not exist.", file=sys.stderr)
    exit(1)

repo = Repo(local_repo)

remote_url = repo.remotes.origin.url

with open(tcfn, "r", encoding="utf-8") as tcf:
    top_cmts = json.load(tcf)

warn_db = []

for top_cmt in alive_it(top_cmts, bar="classic"):
    with open(
        os.path.join(reports, f"report_{top_cmt['id']}.json"), "r", encoding="utf-8"
    ) as trf:
        top_report = json.load(trf)
    prnt_cmt = top_cmt["parents"][0]
    with open(
        os.path.join(reports, f"report_{prnt_cmt}.json"), "r", encoding="utf-8"
    ) as prf:
        prnt_report = json.load(prf)

    diff_report = DeepDiff(prnt_report, top_report, ignore_order=True)

    diff = repo.git.diff(
        prnt_cmt,
        top_cmt["id"],
        "***.java",
        patch=True,
        unified=0,
        src_prefix="./",
        dst_prefix="./",
    )

    if not diff:
        continue

    patch_set = PatchSet(StringIO(diff))

    if "iterable_item_removed" not in diff_report:
        continue

    for path, removed_item in diff_report["iterable_item_removed"].items():
        path_parts = parse_path(path)
        if not (
            len(path_parts) == 4
            and path_parts[0] == "files"
            and path_parts[2] == "violations"
        ):
            continue

        src_fn = prnt_report["files"][int(path_parts[1])]["filename"]

        for patch_file in patch_set:
            if patch_file.source_file != src_fn:
                continue
            for hunk in patch_file:
                if hunk.source_start <= removed_item["beginline"] and removed_item[
                    "beginline"
                ] <= (hunk.source_start + hunk.source_length - 1):
                    for file in top_report["files"]:
                        if file["filename"] == patch_file.target_file:
                            recent_violations = [
                                violation["description"]
                                for violation in file["violations"]
                                if hunk.target_start <= violation["beginline"]
                                and violation["beginline"] <= hunk.target_length
                            ]
                            if removed_item["description"] not in recent_violations:
                                warn = {
                                    "tool": "PMD",
                                    "warning_type": f'{removed_item["ruleset"]}:{removed_item["rule"]}',
                                    "warning_msg": removed_item["description"],
                                    "commit_sha": top_cmt["id"],
                                    "repo": remote_url.split(".git")[0],
                                    "filename": src_fn.replace("./", ""),
                                    "positions": {
                                        "start_line": removed_item["beginline"],
                                        "start_col": removed_item["begincolumn"],
                                        "end_line": removed_item["endline"],
                                        "end_col": removed_item["endcolumn"],
                                    },
                                    "label": 1,
                                }
                                warn_db.append(warn)


with open(output, "w", encoding="utf-8") as o:
    writer = csv.DictWriter(o, fieldnames=HEADERS)
    writer.writeheader()
    writer.writerows(warn_db)
