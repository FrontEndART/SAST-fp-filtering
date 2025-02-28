"""
    This script Analyzes the made XML files, lists the number of commits, where we got at least one of the needed warnings and the number of every warning by warning types.
"""

import json
import sys
import glob
import xml.etree.ElementTree as ET

folder_name = sys.argv[1]
warnings = ["EI_EXPOSE_REP", "EI_EXPOSE_REP2", "FI_PUBLIC_SHOULD_BE_PROTECTED", "MS_EXPOSE_REP", "MS_MUTABLE_ARRAY",
            "MS_MUTABLE_COLLECTION", "MS_MUTABLE_COLLECTION_PKGPROTECT", "MS_SHOULD_BE_FINAL", "NP_NULL_ON_SOME_PATH",
            "NP_NULL_ON_SOME_PATH_EXCEPTION", "NP_NULL_PARAM_DEREF", "NP_NULL_PARAM_DEREF_ALL_TARGETS_DANGEROUS",
            "NP_NULL_PARAM_DEREF_NONVIRTUAL", "SQL_NONCONSTANT_STRING_PASSED_TO_EXECUTE",
            "XSS_REQUEST_PARAMETER_TO_SERVLET_WRITER", ]
warning_types = {}

files = glob.glob(folder_name + "/*/*.xml")

valid_warning_in_commits = 0
all_successful_commits = 0

for file_name in files:
    all_successful_commits += 1
    found = False

    try:
        tree = ET.parse(file_name)
        root = tree.getroot()
    except Exception as e:
        print(e)
        continue

    for bug_instance in root.findall("BugInstance"):
        warning_type = bug_instance.get("type")
        if warning_type not in warnings:
            continue
        found = True
        if warning_type in warning_types:
            warning_types[warning_type] += 1
        else:
            warning_types[warning_type] = 1

    if found:
        valid_warning_in_commits += 1

print("Relevant warning found in " + str(valid_warning_in_commits) + " commits, from " + str(
    all_successful_commits) + " successful commits")
for warning_type in warning_types:
    print(warning_type, warning_types[warning_type])
