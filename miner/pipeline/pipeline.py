#!/usr/bin/env python3

import argparse
import os
import subprocess
import glob
import shutil
import json

COMMIT_DATA_DIR = "commit_data"
DOCKER_IMAGE_NAME = "vfdetector-extended"
DOCKER_CONTAINER_NAME = "vfdetector-container"
VFDETECTOR_DOCKER_DIR = "/VFDetector"
INPUT_DIR = "input"
OUTPUT_DIR = "output"

parser = argparse.ArgumentParser(prog="pipeline", description="Pipeline for VFDetector")

parser.add_argument("-i", "--input", required=True, default="repo_list.txt")
parser.add_argument("-s", "--since", required=False, nargs="?")
parser.add_argument("-u", "--until", required=False, nargs="?")
parser.add_argument("-m", "--memory", required=True)
parser.add_argument("-c", "--chunk-size", required=False)

args = parser.parse_args()

# Read the list of repositories to be analyzed
if not os.path.exists(args.input):
    print("[ERROR]: input file does not exist.")
    exit()

print("Parsing repo URLs...", end="")
with open(args.input, "r", encoding="utf-8") as i:
    repo_urls = i.read().splitlines()
print("Done.")

# Create dir for commit data if not exists
print("Creating dir for commit data...", end="")
if not os.path.exists(COMMIT_DATA_DIR):
    os.mkdir(COMMIT_DATA_DIR)
print("Done.")


# Build docker image
print("Bulding docker image...", end="")
subprocess.run(
    ["docker", "build", "-t", DOCKER_IMAGE_NAME, "."],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.STDOUT,
)
print("Done.")

# Start docker container
print("Starting docker container...", end="")
subprocess.run(
    [
        "docker",
        "run",
        "--name",
        DOCKER_CONTAINER_NAME,
        "-itd",
        "--shm-size",
        args.memory,
        DOCKER_IMAGE_NAME,
    ],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.STDOUT,
)
print("Done.")


# Loop through the repos
for repo_url in repo_urls:

    # Get the name of the project
    project_name = repo_url.split(".git")[0].split("/")[-1]

    print(f"Analyzing project {project_name}...")

    # Create a dir for the project
    name_parts = [project_name, "commit", "data"]
    if args.since:
        name_parts.append("since")
        name_parts.append(args.since.replace("-", "_"))

    if args.until:
        name_parts.append("until")
        name_parts.append(args.until.replace("-", "_"))

    project_data_dir = "_".join(name_parts)

    print("Running diff tool...")

    #  commit data file
    name_parts = [project_name, "commit", "data"]

    command = [os.path.join("..", "diff_tool", "main.py"), "-r", repo_url]

    if args.since:
        command.extend(["-s", args.since])

    if args.until:
        command.extend(["-u", args.until])

    if args.chunk_size:
        command.extend(["-c", args.chunk_size])

    # Run the diff tool on the project
    subprocess.run(command)
    print("End of running diff tool.")

    if not os.path.exists(os.path.join(COMMIT_DATA_DIR, project_data_dir)):
        print("No potential commits, skipping the rest of the analysis.")
        continue

    files = glob.glob(os.path.join(COMMIT_DATA_DIR, project_data_dir, "*.json"))
    os.mkdir(os.path.join(COMMIT_DATA_DIR, project_data_dir, INPUT_DIR))
    for f in files:
        shutil.move(f, os.path.join(COMMIT_DATA_DIR, project_data_dir, INPUT_DIR) + "/")

    os.mkdir(os.path.join(COMMIT_DATA_DIR, project_data_dir, OUTPUT_DIR))

    # Copy the commit data to the docker container from the host
    print("Copying project commit data to docker container...", end="")
    subprocess.run(
        [
            "docker",
            "cp",
            os.path.join(COMMIT_DATA_DIR, project_data_dir),
            DOCKER_CONTAINER_NAME
            + ":"
            + os.path.join(VFDETECTOR_DOCKER_DIR, COMMIT_DATA_DIR)
            + "/",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    print("Done.")

    # Run vfdetector on the commit data
    print("Running VFDetector on project commit data...")

    inputs = os.listdir(os.path.join(COMMIT_DATA_DIR, project_data_dir, "input"))

    for input in inputs:
        print(f"Processing input {input}...")
        output = input.replace("data", "result")

        res = subprocess.run(
            [
                "docker",
                "exec",
                "-w",
                VFDETECTOR_DOCKER_DIR,
                DOCKER_CONTAINER_NAME,
                "python3",
                "application.py",
                "-mode",
                "ranking",
                "-input",
                os.path.join(COMMIT_DATA_DIR, project_data_dir, INPUT_DIR, input),
                "-output",
                os.path.join(COMMIT_DATA_DIR, project_data_dir, OUTPUT_DIR, output),
            ]
        )
        print(f"End of processing input {input}.")
        if res.returncode:
            print(
                f"Execution of VFDetector failed on input {input}. No output was generated."
            )
            continue

    print("End of running VFDetector.")

    res = subprocess.run(
        [
            "docker",
            "exec",
            "-w",
            VFDETECTOR_DOCKER_DIR,
            DOCKER_CONTAINER_NAME,
            "ls",
            os.path.join(COMMIT_DATA_DIR, project_data_dir, OUTPUT_DIR, "*.json"),
        ],
        capture_output=True,
    )


    # Copy the results from the docker container to host
    print("Copying project commit result to host...", end="")
    subprocess.run(
        [
            "docker",
            "cp",
            DOCKER_CONTAINER_NAME
            + ":"
            + os.path.join(
                VFDETECTOR_DOCKER_DIR,
                COMMIT_DATA_DIR,
                project_data_dir,
            ),
            COMMIT_DATA_DIR + "/",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT,
    )
    print("Done.")

    print("Merging results...", end="")
    outputs = os.listdir(os.path.join(COMMIT_DATA_DIR, project_data_dir, OUTPUT_DIR))
    res = []
    for output in outputs:
        with open(
            os.path.join(COMMIT_DATA_DIR, project_data_dir, OUTPUT_DIR, output),
            "r",
            encoding="utf-8",
        ) as o:
            res.extend(json.load(o))

    res.sort(key=lambda x: x["score"], reverse=True)
    with open(
        os.path.join(
            COMMIT_DATA_DIR,
            project_data_dir,
            project_data_dir.replace("data", "result") + ".json",
        ),
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(res, f)
    print("Done.")

    print(f"End of analyzing project {project_name}.")


# Stop docker container
print("Stopping docker container...", end="")
subprocess.run(
    ["docker", "stop", DOCKER_CONTAINER_NAME],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.STDOUT,
)
print("Done.")

# Remove docker container
print("Removing docker container...", end="")
subprocess.run(
    ["docker", "container", "rm", DOCKER_CONTAINER_NAME],
    stdout=subprocess.DEVNULL,
    stderr=subprocess.STDOUT,
)
print("Done.")
