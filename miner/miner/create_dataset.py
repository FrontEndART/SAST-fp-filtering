#!/usr/bin/env python3

import glob
import os
import pandas as pd
import shutil

def get_records(project, sca, category):
    if not os.path.exists(os.path.join(project, f"{sca}_{category}_warn_db.csv")):
        return None
    
    df = pd.read_csv(os.path.join(project, f"{sca}_{category}_warn_db.csv"))

    project_name = project.split(os.sep)[-1]

    df["filepath"] =  df["filepath"].apply(lambda fp: fp.replace("dataset", f"files/{project_name}"))

    return df

if not os.path.exists("files"):
    os.mkdir("files")

dataset_sources = []

for project in glob.glob(os.path.join("warn_db", "*")):

    project_name = project.split(os.sep)[-1]

    if not os.path.exists(f"files/{project_name}"):
        os.mkdir(f"files/{project_name}")

    if os.path.exists(os.path.join(project, "dataset")):
        shutil.copytree(os.path.join(project, "dataset"), f"files/{project_name}", dirs_exist_ok=True)
    
    pmd_fp = get_records(project, "pmd", "fp")
    if pmd_fp is not None:
        dataset_sources.append(pmd_fp)
    pmd_tp = get_records(project, "pmd", "tp")
    if pmd_tp is not None:
        dataset_sources.append(pmd_tp)
    spotbugs_fp = get_records(project, "spotbugs", "fp")
    if spotbugs_fp is not None:
        dataset_sources.append(spotbugs_fp)
    spotbugs_tp = get_records(project, "spotbugs", "tp")
    if spotbugs_tp is not None:
        dataset_sources.append(spotbugs_tp)

    

    
dataset = pd.concat(dataset_sources, ignore_index=True)

dataset.drop(["Unnamed: 0"], axis=1, inplace=True)
dataset.index.name = "ID"

dataset.to_parquet("dataset.parquet")