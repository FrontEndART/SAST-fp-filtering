import json
import os
from datetime import timezone


def create_warn(tool, repo_url, commit_sha, commit_date, violation, filepath, label):
    if tool == "PMD":
        return {
            "tool": tool,
            "warning_type": f'{violation["ruleset"]}:{violation["rule"]}',
            "warning_msg": violation["description"],
            "commit_sha": commit_sha,
            "repo": repo_url,
            "filename": os.path.basename(filepath),
            "positions": str(
                {
                    "start_line": violation["beginline"],
                    "start_col": violation["begincolumn"],
                    "end_line": violation["endline"],
                    "end_col": violation["endcolumn"],
                }
            ),
            "filepath": filepath,
            "commit_date": commit_date,
            "label": label,
        }
    else:
        return {
            "tool": tool,
            "warning_type": violation.get("type"),
            "warning_msg": violation.find("ShortMessage").text,
            "commit_sha": commit_sha,
            "repo": repo_url,
            "filename": os.path.basename(filepath),
            "positions": str(
                {
                    "start_line": (
                        violation.find("SourceLine").get("start")
                        if violation.find("SourceLine").get("start")
                        else violation.find("Class").find("SourceLine").get("start")
                    ),
                    "start_col": "",
                    "end_line": (
                        violation.find("SourceLine").get("end")
                        if violation.find("SourceLine").get("end")
                        else violation.find("Class").find("SourceLine").get("end")
                    ),
                    "end_col": "",
                }
            ),
            "filepath": filepath,
            "commit_date": commit_date,
            "label": label,
        }


def report_to_dict(report_file):
    with open(report_file, "r", encoding="utf-8") as rf:
        report = json.load(rf)

    violations = {}
    if not report["files"]:
        return violations

    for file in report["files"]:
        violations[file["filename"]] = file["violations"]
    return violations


def get_iso_commit_date(commit):
    return (
        commit.committed_datetime.astimezone(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )
