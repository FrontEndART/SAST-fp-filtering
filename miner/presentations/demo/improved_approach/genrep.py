#!/usr/bin/python3

import argparse
import os
import sys
import json
import subprocess

import pathlib

from git import Repo

from alive_progress import alive_it

parser = argparse.ArgumentParser(prog="genrep", description="Generate PMD reports")

parser.add_argument("--local-repo", required=True, nargs=1, type=pathlib.Path)
parser.add_argument("--commit-file", required=True, nargs=1, type=pathlib.Path)
parser.add_argument("--ruleset-file", required=True, nargs=1, type=pathlib.Path)
parser.add_argument("--output-dir", required=True, nargs=1, type=pathlib.Path)


# Parsing arguments
args = parser.parse_args()

local_repo = str(args.local_repo[0])
commit_file = str(args.commit_file[0])
ruleset_file = str(args.ruleset_file[0])
output_dir = str(args.output_dir[0])


if not os.path.exists(local_repo):
    print(
        f"[ERROR]: Local repository {local_repo} does not exist.",
        file=sys.stderr,
    )
    exit(1)


if not os.path.exists(commit_file):
    print(
        f"[ERROR]: Top commits file {commit_file} does not exist.",
        file=sys.stderr,
    )
    exit(1)


if not os.path.exists(ruleset_file):
    print(f"[ERROR]: Ruleset file {ruleset_file} does not exists.", file=sys.stderr)
    exit(1)

repository = Repo(local_repo)

commit_hashes = set()
with open(commit_file, "r", encoding="utf-8") as f:
    data = json.load(f)
    for entry in data:
        commit_hashes.add(entry["id"])
        if entry["parents"]:
            commit_hashes.update(entry["parents"])

print(
    f"{len(commit_hashes)} distinct commit hashes {'were' if len(commit_hashes) > 1 else 'was'} found."
)


for commit_hash in alive_it(commit_hashes, bar="classic"):
    repository.git.checkout(commit_hash)
    report_filename = f"report_{commit_hash}.json"
    subprocess.run(
        [
            "pmd",
            "check",
            "--cache",
            os.path.join(output_dir, "cache"),
            "--dir",
            local_repo,
            "--rulesets",
            ruleset_file,
            "--format",
            "json",
            "--report-file",
            os.path.join(output_dir, report_filename),
            "--no-progress",
        ]
    )
