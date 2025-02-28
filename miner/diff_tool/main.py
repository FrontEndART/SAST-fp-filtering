#!/usr/bin/env python3

import os
import argparse
import shutil
import json

from loguru import logger

from git import Repo
from git.exc import GitCommandError
from alive_progress import alive_it

from GitRemoteProgress import GitRemoteProgress


base_path = os.path.dirname(os.path.abspath(__file__))

REPO_DIR = base_path + "/repo_dir"

COMMIT_DATA_DIR = "commit_data"

DEFAULT_CHUNK_SIZE = 10


parser = argparse.ArgumentParser(
    prog="DiffTool", description="Diff Tool to create input for VFDetector"
)

parser.add_argument("-r", "--repository", required=True)
parser.add_argument("-s", "--since", required=False, nargs="?")
parser.add_argument("-u", "--until", required=False, nargs="?")
parser.add_argument(
    "-c",
    "--chunk-size",
    required=False,
    nargs="?",
    type=int,
    default=DEFAULT_CHUNK_SIZE,
)

if not os.path.exists(REPO_DIR):
    os.mkdir(REPO_DIR)

args = parser.parse_args()

repo_name = args.repository.split(".git")[0].split("/")[-1]


print("Cloning repository...")
try:
    repo = Repo.clone_from(
        url=args.repository,
        to_path=os.path.join(REPO_DIR, repo_name),
        progress=GitRemoteProgress(),
    )
except GitCommandError as e:
    logger.error(f"Message: {e.stderr}")
    exit()
print("End of cloning repository.")


commits = list(
    repo.iter_commits(repo.head.name, reverse=True, since=args.since, until=args.until)
)

results = []


print("Processing commits...")

bar = alive_it(range(len(commits) - 1), bar="classic")
for i in bar:
    previous_commit = commits[i]
    new_commit = commits[i + 1]

    diff = repo.git.diff(
        "--no-renames",
        "--patch",
        "--unified=0",
        previous_commit,
        new_commit,
        "***.java",
    )

    if diff:
        lines = diff.splitlines()

        relevant_lines = [
            l
            for l in lines
            if l.startswith(("+", "-", "@")) and not l.startswith(("--- a/", "+++ b/"))
        ]

        patches = []

        buf = []
        for l in relevant_lines:
            if l.startswith("@"):
                if buf:
                    patches.append("\n".join(buf))
                buf = [l]
            else:
                buf.append(l)
        patches.append("\n".join(buf))

        result = {
            "id": new_commit.hexsha,
            "message": new_commit.message,
            "patch": patches,
        }
        results.append(result)
print("End of processing commits.")


if results:
    if len(results) == 1:
        message = "1 potential commit was found."
    else:
        message = f"{len(results)} potential commits were found."
    print(message)
    print("Exporting commit data...")

    name_parts = [repo_name, "commit", "data"]
    if args.since:
        name_parts.append("since")
        name_parts.append(args.since.replace("-", "_"))

    if args.until:
        name_parts.append("until")
        name_parts.append(args.until.replace("-", "_"))

    project_data_dir = "_".join(name_parts)

    os.mkdir(os.path.join(COMMIT_DATA_DIR, project_data_dir))

    chunk_size = args.chunk_size if args.chunk_size > 0 else DEFAULT_CHUNK_SIZE
    num_of_chunks = len(results) // chunk_size + 1
    for i in alive_it(range(num_of_chunks), bar="classic"):
        chunk = results[i * chunk_size : (i + 1) * chunk_size]
        fn_parts = [repo_name, "commit", "data", chunk[0]["id"][:7], chunk[-1]["id"][:7]]
        fn = "_".join(fn_parts) + ".json"
        with open(
            os.path.join(COMMIT_DATA_DIR, project_data_dir, fn), "w", encoding="utf-8"
        ) as output:
            json.dump(chunk, output)
    print("End of exporting commit data.")
else:
    print("No potential commits were found. No output was generated.")


shutil.rmtree(REPO_DIR)
