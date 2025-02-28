#!/usr/bin/env python3

import argparse
import glob
import os.path
import pathlib
import shutil
import sys

import pandas as pd
from alive_progress import alive_it
from git import Repo
from loguru import logger

logger.remove(0)
logger.add(sys.stderr, format="<green>{time:YYYY.MM.DD. HH:mm:ss}</green> <bold>[{level}]</bold>: {message}",
           colorize=True)

parser = argparse.ArgumentParser(prog="cadet", description="Create dataset")

parser.add_argument("--local-repo", required=True, nargs=1, type=pathlib.Path)
parser.add_argument("--warn-db-dir", required=True, nargs=1, type=pathlib.Path)
parser.add_argument("--dataset-dir", required=True, nargs=1, type=pathlib.Path)
parser.add_argument("--sca", required=True, nargs=1, choices=["pmd", "spotbugs"])

args = parser.parse_args()

local_repo = str(args.local_repo[0])
warn_db_dir = str(args.warn_db_dir[0])
dataset_dir = str(args.dataset_dir[0])
sca = args.sca[0]

if not os.path.exists(local_repo):
    logger.error(f"Local repository {local_repo} does not exist.")
    exit(1)

if not os.path.exists(warn_db_dir):
    logger.error(f"Warning database directory {warn_db_dir} does not exist.")
    exit(1)

if not os.path.exists(dataset_dir):
    logger.error(f"Dataset directory {dataset_dir} does not exist.")
    exit(1)


warn_db_files = glob.glob(os.path.join(warn_db_dir, f"{sca}_?p_warn_db.csv"))

if len(warn_db_files) < 1:
    logger.error(f"There are no warning database files in directory {warn_db_dir}.")
    exit(1)

logger.info(f"Found {len(warn_db_files)} warning database file{'s' if len(warn_db_files) > 1 else ''}.")

os.chdir(local_repo)

repo = Repo(".")

for warn_db_file in alive_it(warn_db_files, title="Creating dataset", bar="classic"):
    warn_db = pd.read_csv(warn_db_file)

    for warn in warn_db.itertuples():

        if not os.path.exists(os.path.join(dataset_dir, warn.commit_sha, os.path.dirname(warn.filepath))):
            os.makedirs(os.path.join(dataset_dir, warn.commit_sha, os.path.dirname(warn.filepath)))

        if not os.path.exists(os.path.join(dataset_dir, warn.commit_sha, warn.filepath)):
            repo.git.checkout(warn.commit_sha)
            shutil.copy2(warn.filepath, os.path.join(dataset_dir, warn.commit_sha, warn.filepath))
            repo.git.clean("-xdfq")

        warn_db.loc[warn.Index, 'filepath'] = os.path.join("dataset", warn.commit_sha, warn.filepath)

    warn_db.to_csv(warn_db_file)

os.chdir(os.path.dirname(os.path.abspath(__file__)))
