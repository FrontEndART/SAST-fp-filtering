#!/usr/bin/env python3

import argparse
import pathlib
import os
import glob
import json
import sys

from git import Repo
from alive_progress import alive_it
from loguru import logger

logger.remove(0)
logger.add(sys.stderr, format="<green>{time:YYYY.MM.DD. HH:mm:ss}</green> <bold>[{level}]</bold>: {message}",
           colorize=True)

DFLT_ENC = "utf-8"

parser = argparse.ArgumentParser(prog="skip", description="Skipping ranking commits")

parser.add_argument("--local-repo", required=True, nargs=1, type=pathlib.Path)
parser.add_argument("--code-change-dir", required=True, nargs=1, type=pathlib.Path)
parser.add_argument("--output", required=True, nargs=1, type=pathlib.Path)

args = parser.parse_args()

local_repo = args.local_repo[0]
code_change_dir = args.code_change_dir[0]
output = args.output[0]

if not os.path.exists(local_repo):
    logger.error(f"Local repo {local_repo} does not exist.")
    exit(1)

if not os.path.exists(code_change_dir):
    logger.error(f"Code change dir {code_change_dir} does not exist.")
    exit(1)


code_change_files = glob.glob(os.path.join(code_change_dir, "*"))

repo = Repo(local_repo)

commit_list = []

for code_change_file in alive_it(code_change_files, title="Generating commit list", bar="classic"):
    with open(code_change_file, "r", encoding=DFLT_ENC) as chf:
        code_changes = json.load(chf)

    for code_change in code_changes:
        commit = repo.commit(code_change["id"])
        commit_list.append({
            "id": code_change["id"],
            "parents": [parent.hexsha for parent in commit.parents]
        })

with open(output, "w", encoding=DFLT_ENC) as o:
    json.dump(commit_list, o)
        

