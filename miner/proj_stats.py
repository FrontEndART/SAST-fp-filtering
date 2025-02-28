#!/usr/bin/env python3

import glob
import os
import pandas as pd
from tabulate import tabulate

stats = pd.DataFrame(
    columns=["project", "pmd_fp", "pmd_tp", "spotbugs_fp", "spotbugs_tp"]
)


def get_records(project, sca, category):
    if not os.path.exists(os.path.join(project, f"{sca}_{category}_warn_db.csv")):
        return None

    return len(pd.read_csv(os.path.join(project, f"{sca}_{category}_warn_db.csv")))


for project in glob.glob(os.path.join("warn_db", "*")):
    project_name = project.split(os.sep)[-1]
    pmd_fp = get_records(project, "pmd", "fp")
    pmd_tp = get_records(project, "pmd", "tp")
    spotbugs_fp = get_records(project, "spotbugs", "fp")
    spotbugs_tp = get_records(project, "spotbugs", "tp")

    stats.loc[-1] = {
        "project": project_name,
        "pmd_fp": pmd_fp,
        "pmd_tp": pmd_tp,
        "spotbugs_fp": spotbugs_fp,
        "spotbugs_tp": spotbugs_tp,
    }
    stats.index = stats.index + 1
    stats = stats.sort_index()

stats.sort_values(by="project", inplace=True, key=lambda col: col.str.lower())

analyzed_projects = len(stats)

stats.loc["Total"] = stats[["pmd_fp", "pmd_tp", "spotbugs_fp", "spotbugs_tp"]].sum()
stats.loc["Total", "project"] = "TOTAL"

data = stats.to_dict("records")
data.insert(-1, {})

print()
print("Project Statistics:")
print(tabulate(data, headers="keys", showindex=False, tablefmt="psql", intfmt=","))
print()

print("Analyzed projects:", analyzed_projects)
total_fp = stats.loc["Total", "pmd_fp"] + stats.loc["Total", "spotbugs_fp"]
print("TOTAL FP:", "{:,}".format(total_fp))
total_tp = stats.loc["Total", "pmd_tp"] + stats.loc["Total", "spotbugs_tp"]
print("TOTAL TP:", "{:,}".format(total_tp))
print("TOTAL:", "{:,}".format(total_fp + total_tp))


stats.to_csv("proj_stats.csv", index=False)
