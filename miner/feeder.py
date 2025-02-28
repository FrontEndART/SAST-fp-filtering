#!/usr/bin/env python3

import argparse
import datetime
import os
import pathlib
import subprocess
import sys

from loguru import logger


# a custom logger for our purposes
logger.remove(0)
logger.add(
    sys.stderr,
    format="<green>{time:YYYY.MM.DD. HH:mm:ss}</green> <bold>[{level}]</bold>: {message}",
    colorize=True,
)

parser = argparse.ArgumentParser(
    prog="feeder", description="A program to feed the miner"
)

parser.add_argument("--repo-list", required=True, nargs=1, type=pathlib.Path)
parser.add_argument("--limit", required=False, nargs="?", type=int)
parser.add_argument(
    "--since", required=False, nargs="?", type=datetime.date.fromisoformat
)
parser.add_argument(
    "--until", required=False, nargs="?", type=datetime.date.fromisoformat
)
parser.add_argument("--pmd", required=False, action="store_true")
parser.add_argument("--spotbugs", required=False, action="store_true")

args = parser.parse_args()

repo_list = str(args.repo_list[0])
limit = args.limit if "limit" in args else None
since = args.since if "since" in args else None
until = args.until if "until" in args else None

if not os.path.exists(repo_list):
    logger.error(f"Repo list file {repo_list} does not exist.")
    exit(1)

with open(repo_list, "r", encoding="utf-8") as rlf:
    repo_urls = rlf.readlines()

for repo_url in repo_urls:
    cmd = [
        "python3"
        "miner.py",
        "--repo-url",
        repo_url.strip(),
    ]

    if limit:
        cmd.extend(["--limit", limit])

    if since:
        cmd.extend(["--since", str(since)])

    if until:
        cmd.extend(["--until", str(until)])

    if args.pmd:
        cmd.extend(["--pmd"])

    if args.spotbugs:
        cmd.extend(["--spotbugs"])

    subprocess.run(cmd)
