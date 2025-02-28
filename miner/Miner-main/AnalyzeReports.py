"""
    This script Analyzes the made reports, lists the number of successful commits and the number of every fails by error types.
"""

import json
import sys
import glob

folder_name = sys.argv[1]
number_of_commits = 0
successful_commits = 0
fixes = 0
skipped_commit = 0
build_fail = 0
git_fail = 0
spotbugs_fail = 0
unknown_fail = 0
tracker_fail = 0

for file_name in glob.glob(folder_name + "/*.json"):
    try:
        with open(file_name, "r") as f:
            data = json.load(f)
    except Exception as e:
        print("unfinished report: ", file_name)

    for commit in data:
        number_of_commits += 1
        status = commit["status"]
        tracker_msg = commit["tracker"]

        if status == "successful":
            if "found" in tracker_msg:
                fixes += 1
            elif "Tracker failed" in tracker_msg:
                tracker_fail += 1
            else:
                successful_commits += 1
        elif status == "skipped" or status == "skipping":
            skipped_commit += 1
        elif status == "build failed":
            build_fail += 1
        elif status == "Git error":
            git_fail += 1
        elif status == "SB failed":
            spotbugs_fail += 1
        elif status == "unknown":
            unknown_fail += 1

print("All commits: ", number_of_commits)
print("Successful commits: ", successful_commits)
print("Fixes: ", fixes)
print("Skipped commit: ", skipped_commit)
print("Build fail: ", build_fail)
print("Git fail: ", git_fail)
print("Spotbugs fail: ", spotbugs_fail)
print("Unknown fail: ", unknown_fail)
print("Tracker fail: ", tracker_fail)
