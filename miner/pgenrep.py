#!/usr/bin/env python3

import argparse
import datetime
import os
import pathlib
import subprocess
import sys
import tarfile

from alive_progress import alive_it
from git import Repo
from loguru import logger


logger.remove(0)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY.MM.DD. HH:mm:ss}</green> <bold>[{level}]</bold>: {message}",
    colorize=True,
)

parser = argparse.ArgumentParser(prog="pgenrep", description="Generate PMD reports")

parser.add_argument("--local-repo", required=True, nargs=1, type=pathlib.Path)
parser.add_argument("--ruleset-file", required=True, nargs=1, type=pathlib.Path)
parser.add_argument("--output-dir", required=True, nargs=1, type=pathlib.Path)
parser.add_argument(
    "--since", required=False, nargs="?", type=datetime.date.fromisoformat
)
parser.add_argument(
    "--until", required=False, nargs="?", type=datetime.date.fromisoformat
)

# Parsing arguments
args = parser.parse_args()

local_repo = str(args.local_repo[0])
ruleset_file = str(args.ruleset_file[0])
output_dir = str(args.output_dir[0])
since = args.since if "since" in args else None
until = args.until if "until" in args else None

if not os.path.exists(local_repo):
    logger.error(f"Local repository {local_repo} does not exist.")
    exit(1)

if not os.path.exists(ruleset_file):
    logger.error(f"Ruleset file {ruleset_file} does not exists.")
    exit(1)

repo = Repo(local_repo)

commits = list(
    repo.iter_commits(repo.head.name, reverse=True, since=since, until=until)
)

for commit in alive_it(commits, title="Generating PMD reports", bar="classic"):
    if not os.path.exists(os.path.join(output_dir, f"report_{commit.hexsha[:7]}.tar.gz")):
        repo.git.checkout(commit)
        report_filename = f"report_{commit.hexsha[:7]}.json"
        
        try:
            pmd_out = subprocess.run(
                [
                    "pmd",
                    "check",
                    "--relativize-paths-with",
                    local_repo,
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
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=300
            )
        except subprocess.TimeoutExpired:
             logger.warning(f"Failed to generate PMD report for files of commit {commit.hexsha[:7]} due to timeout.")
             continue

        if not os.path.exists(os.path.join(output_dir, report_filename)):
            logger.warning(
                f"Failed to generate PMD report for files of commit {commit.hexsha[:7]}."
            )
        else:
            report_tar_gz = os.path.join(
                output_dir, report_filename.replace("json", "tar.gz")
            )
            with tarfile.open(report_tar_gz, "w:gz") as targz:
                targz.add(os.path.join(output_dir, report_filename), report_filename)

            if not os.path.exists(report_tar_gz):
                logger.warning(
                    f"Failed to generate compressed PMD report for files of commit {commit.hexsha[:7]}."
                )
            else:
                os.remove(os.path.join(output_dir, report_filename))
