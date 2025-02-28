#!/usr/bin/python3

import argparse
import os
import sys
import json
import pathlib

from git import Repo

DEFAULT_LIMIT = 1

parser = argparse.ArgumentParser(
    prog="Top Commits",
    description="Get top commits and their direct parents",
)

parser.add_argument("--commit-rank", required=True, nargs=1, type=pathlib.Path)
parser.add_argument("--local-repo", required=True, nargs=1, type=pathlib.Path)
parser.add_argument("--output", required=True, nargs=1, type=pathlib.Path)
parser.add_argument("--limit", required=False, nargs="?", type=int)


args = parser.parse_args()

top_cmts = args.commit_rank[0]
local_repo = args.local_repo[0]
output = args.output[0]

if args.limit:
    if args.limit < DEFAULT_LIMIT:
        limit = DEFAULT_LIMIT
    else:
        limit = args.limit
else:
    limit = None


if not os.path.exists(top_cmts):
    print(
        f"[ERROR]: Commit rankings file {top_cmts} does not exist.",
        file=sys.stderr,
    )
    exit(1)

if not os.path.exists(local_repo):
    print(f"[ERROR]: Local repo {local_repo} does not exist.", file=sys.stderrr)
    exit(1)

if os.path.exists(output):
    print(f"[ERROR]: Output file {output} already exists.", file=sys.stderr)
    exit(1)


with open(top_cmts, "r", encoding="utf-8") as crf:
    cmt_ranks = json.load(crf)

top_cmts = [item["id"] for item in (cmt_ranks[:limit] if limit else cmt_ranks)]

repo = Repo(local_repo)

data = [
    {"id": cmt, "parents": [parent.hexsha for parent in repo.commit(cmt).parents]}
    for cmt in top_cmts
]

with open(output, "w", encoding="utf-8") as tcf:
    json.dump(data, tcf)
