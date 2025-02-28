#!/usr/bin/env python3

import os
import argparse
import json
import sys

from pathlib import Path
from datetime import date

from git import Repo
from io import StringIO
from unidiff import PatchSet

from math import ceil

from alive_progress import alive_it

DEFAULT_CHUNK_SIZE = 10

parser = argparse.ArgumentParser(
    prog="DiffTool", description="Diff tool to create input for VFDetector"
)

parser.add_argument("--local-repository", required=True, nargs=1, type=Path)
parser.add_argument("--output-dir", required=True, nargs=1, type=Path)
parser.add_argument("--since", required=False, nargs="?", type=date.fromisoformat)
parser.add_argument("--until", required=False, nargs="?", type=date.fromisoformat)
parser.add_argument(
    "--chunk-size",
    required=False,
    nargs="?",
    type=int,
    default=DEFAULT_CHUNK_SIZE,
)

# Parsing arguments
args = parser.parse_args()

local_repository = args.local_repository[0]
output_dir = args.output_dir[0]
since = args.since if "since" in args else None
until = args.until if "until" in args else None
chunk_size = (
    args.chunk_size
    if "chunk_size" in args and args.chunk_size > 0
    else DEFAULT_CHUNK_SIZE
)


if not os.path.exists(local_repository):
    print(
        f"[ERROR]: Local repository {local_repository} does not exist.", file=sys.stderr
    )
    exit(1)

if not os.path.exists(output_dir):
    print(
        f"[ERROR]: Directory {output_dir} does not exist.",
        file=sys.stderr,
    )
    exit(1)


repo = Repo(local_repository)

commits = list(
    repo.iter_commits(repo.head.name, reverse=True, since=since, until=until)
)


commit_changes = []


print("Processing commits...")
bar = alive_it(range(len(commits) - 1), bar="classic")
for i in bar:
    previous_commit = commits[i]
    new_commit = commits[i + 1]

    diff = repo.git.diff(previous_commit, new_commit, "***.java", unified=0)

    if not diff:
        continue

    patch_set = PatchSet(StringIO(diff))

    patches = []
    for patch_file in patch_set:
        for hunk in patch_file:
            patches.append(str(hunk))

    result = {
        "id": new_commit.hexsha,
        "message": new_commit.message,
        "patch": "\n".join(patches),
    }
    commit_changes.append(result)
print("End of processing commits.")


if not commit_changes:
    print("[WARNING]: No potential commits were found. No output was generated.")
    exit()

print(
    f"{len(commit_changes)} commit changes {'were' if len(commit_changes) > 1 else 'was'} found."
)

print("Exporting commit changes...")
num_of_chunks = ceil(len(commit_changes) / chunk_size)
for i in alive_it(range(num_of_chunks), bar="classic"):
    chunk = commit_changes[i * chunk_size : (i + 1) * chunk_size]
    filename = f'code_change_{chunk[0]["id"][:7]}_{chunk[-1]["id"][:7]}.json'
    with open(
        os.path.join(output_dir, filename),
        "w",
        encoding="utf-8",
    ) as output:
        json.dump(chunk, output)
print("End of exporting commit changes.")
