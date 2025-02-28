#!/usr/bin/env python3


import glob
import os
import pandas as pd
from tabulate import tabulate


def create_db(category):
    dfs = []
    for db in glob.glob(os.path.join("warn_db", "*", f"pmd_{category}_warn_db.csv")):
        df = pd.read_csv(db)
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


def count(row, db):
    return len(db[db["warning_type"].str.contains(row["category"])])


fp_db = create_db("fp")
tp_db = create_db("tp")


stats = pd.read_csv("pmd_main_bug_categories.csv")

stats["fp"] = stats.apply(count, axis=1, args=[fp_db])

fp_sum = stats["fp"].sum()

stats["fp_%"] = stats["fp"] / fp_sum

stats["tp"] = stats.apply(count, axis=1, args=[tp_db])

tp_sum = stats["tp"].sum()

stats["tp_%"] = stats["tp"] / tp_sum


stats.loc["Total"] = stats[["fp", "fp_%", "tp", "tp_%"]].sum()
stats.loc["Total", "category"] = "TOTAL"

stats["fp"] = stats["fp"].astype("int64")
stats["tp"] = stats["tp"].astype("int64")

data = stats.to_dict("records")
data.insert(-1, {})

print()
print("PMD Statistics:")
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

stats.to_csv("pmd_stats.csv", index=False)
