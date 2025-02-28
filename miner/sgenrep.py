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
logger.add(sys.stderr, format="<green>{time:YYYY.MM.DD. HH:mm:ss}</green> <bold>[{level}]</bold>: {message}",
           colorize=True)

parser = argparse.ArgumentParser(prog="genrep", description="Generate Spotbugs reports")

parser.add_argument("--local-repo", required=True, nargs=1, type=pathlib.Path)
parser.add_argument("--dependency-dir", required=True, nargs=1, type=pathlib.Path)
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
dependency_dir = str(args.dependency_dir[0])
output_dir = str(args.output_dir[0])
since = args.since if "since" in args else None
until = args.until if "until" in args else None

if not os.path.exists(local_repo):
    logger.error(f"Local repository {local_repo} does not exist.")
    exit(1)

if not os.path.exists(dependency_dir):
    logger.error(f"Local dependency repository {dependency_dir} does not exist.")
    exit(1)

repo = Repo(local_repo)

commits = list(
    repo.iter_commits(repo.head.name, reverse=True, since=since, until=until)
)

os.chdir(local_repo)

gradle_cmd = ["-q", "-g", dependency_dir, "clean", "build", "-x", "test"]
gradle_auxclasspath = os.path.join(dependency_dir, "caches", "modules-2", "files-2.1")

mvn_cmd = ["-q", "-U", "-T", "1C", "clean", "package",
           "-Dmaven.test.skip=true", "-DskipTests", "-Dmaven.javadoc.skip=true",
           "-Dsource.skip", f"-Dmaven.repo.local={dependency_dir}"]
mvn_auxclasspath = dependency_dir

for commit in alive_it(commits, title="Generating Spotbugs reports",
                       bar="classic"):

    repo.git.checkout(commit)

    if os.path.exists("gradlew"):
        build_cmd = ["./gradlew"] + gradle_cmd
        auxclasspath = gradle_auxclasspath
    elif os.path.exists("build.gradle"):
        build_cmd = ["gradle"] + gradle_cmd
        auxclasspath = gradle_auxclasspath
    elif os.path.exists("mvnw"):
        build_cmd = ["./mvnw"] + mvn_cmd
        auxclasspath = mvn_auxclasspath
    elif os.path.exists("pom.xml"):
        build_cmd = ["mvn"] + mvn_cmd
        auxclasspath = mvn_auxclasspath
    else:
        logger.error(f"Failed to build commit {commit.hexsha[:7]}.")
        repo.git.clean("-xdfq")
        repo.git.execute(["git", "restore", "."])
        continue
        
    try:
    
        build_out = subprocess.run(build_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1200)

        if build_out.returncode:
            logger.warning(f"Failed to build commit {commit.hexsha[:7]}.")
            repo.git.clean("-xdfq")
            repo.git.execute(["git", "restore", "."])
            continue

        report_filename = f"report_{commit.hexsha[:7]}.xml"
        spotbugs_out = subprocess.run(
            [
                "spotbugs",
                "-textui",
                f"-xml:withMessages={os.path.join(output_dir, report_filename)}",
                "-maxHeap",
                "4096",
                "-low",
                "-effort:max",
                "-auxclasspath",
                auxclasspath,
                "."
            ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=1200
        )
            
    except subprocess.TimeoutExpired as e:
        logger.warning(f"Failed to generate Spotbugs report for files of commit {commit.hexsha[:7]} due to timeout.")
        continue

    if not os.path.exists(os.path.join(output_dir, report_filename)):
        logger.warning(f"Failed to generate Spotbugs report for files of commit {commit.hexsha[:7]}.")
    else:
        report_tar_gz = os.path.join(
            output_dir, report_filename.replace("xml", "tar.gz")
        )
        with tarfile.open(report_tar_gz, "w:gz") as targz:
            targz.add(os.path.join(output_dir, report_filename), report_filename)

        if not os.path.exists(report_tar_gz):
            logger.warning(
                f"Failed to generate compressed PMD report for files of commit {commit.hexsha[:7]}."
            )
        else:
            os.remove(os.path.join(output_dir, report_filename))

    repo.git.clean("-xdfq")
    repo.git.execute(["git", "restore", "."])

os.chdir(os.path.abspath(os.path.dirname(__file__)))
