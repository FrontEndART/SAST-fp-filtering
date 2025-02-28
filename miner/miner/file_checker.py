#!/usr/bin/env python3

import os
import glob
import pandas as pd

projects_with_incomplete_dataset = set()

os.chdir("warn_db")
for project in glob.glob("*"):
    os.chdir(project)
    for csv in glob.glob("*.csv"):
        db = pd.read_csv(csv)
        files = db["filepath"].to_list()
        for file in files:
            if not os.path.exists(file):
                projects_with_incomplete_dataset.add(project)
    os.chdir("..")
    
if projects_with_incomplete_dataset:
    print(projects_with_incomplete_dataset)