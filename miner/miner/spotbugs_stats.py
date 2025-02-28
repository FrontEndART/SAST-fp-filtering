#!/usr/bin/env python3

import glob
import os
import pandas as pd
from tabulate import tabulate


def create_db(category):
    dfs = []
    for db in glob.glob(
        os.path.join("warn_db", "*", f"spotbugs_{category}_warn_db.csv")
    ):
        df = pd.read_csv(db)
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


def count(row, db):
    return len(db[db["category"] == row["category"]])


fp_db = create_db("fp")
tp_db = create_db("tp")

types = pd.read_csv("spotbugs_bug_types.csv")

ext_fp = pd.merge(fp_db, types, on="warning_type")
ext_tp = pd.merge(tp_db, types, on="warning_type")

stats = pd.read_csv("spotbugs_main_bug_categories.csv")

stats["fp"] = stats.apply(count, axis=1, args=[ext_fp])

fp_sum = stats["fp"].sum()

stats["fp_%"] = stats["fp"] / fp_sum

stats["tp"] = stats.apply(count, axis=1, args=[ext_tp])

tp_sum = stats["tp"].sum()

stats["tp_%"] = stats["tp"] / tp_sum


stats.loc["Total"] = stats[["fp", "fp_%", "tp", "tp_%"]].sum()
stats.loc["Total", "category"] = "TOTAL"


stats["fp"] = stats["fp"].astype("int64")
stats["tp"] = stats["tp"].astype("int64")

data = stats.to_dict("records")
data.insert(-1, {})

print()
print("Spotbugs Statistics:")
print(
    tabulate(
        data,
        headers="keys",
        showindex=False,
        tablefmt="psql",
        intfmt=",",
        floatfmt=".4%",
    )
)
print()
print("TOTAL:", "{:,}".format(stats.loc["Total", "fp"] + stats.loc["Total", "tp"]))

stats.to_csv("spotbugs_stats.csv", index=False)
