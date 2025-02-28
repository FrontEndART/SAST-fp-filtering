import json
import pickle
from typing import Any
import ast
from pathlib import Path

import pandas as pd

import config


def extract_code(filepath, positions, context_size = config.CONTEXT_SIZE, offset=-1):
    """Extract code parts from the file based on the given positions."""
    with filepath.open(encoding="utf-8", errors="ignore") as file:
        lines = file.readlines()

        if not positions["start_line"] or not positions["end_line"]:
            return ""
        
        start_line = int(positions["start_line"]) - context_size + offset
        
        if start_line < 1 + offset:
            start_line = 1 + offset
        
        end_line = int(positions["end_line"]) + context_size + offset
        
        if len(lines) + offset < end_line:
            end_line = len(lines) + offset 

        code_parts = (
            res.split(r"//")[0].strip() for res in lines[start_line : end_line + 1]
        )  # remove comments
    return "\n".join(code_parts)


def process_row(row: pd.Series) -> str:
    """Parse the code parts given by the filepath and positions."""
    filepath = Path(config.FILES_PATH) / row["filepath"]
    positions = ast.literal_eval(row["positions"])
    code = extract_code(filepath, positions)

    return code


def process_row_labeled(row: pd.Series) -> str:
    """Parse the code parts given by the filepath and positions with
    the vulnerability label and warning message appended."""

    filepath = Path(config.FILES_PATH) / row["filepath"]
    positions = ast.literal_eval(row["positions"])
    code = extract_code(filepath, positions)

    return code + f" <LABEL {row['label']}>" + f" MSG {row['warning_msg']}"


def load_pkl(filename: str | Path):
    with Path(filename).open("rb") as f:
        return pickle.load(f)


def save_pkl(filename: str | Path, obj: Any):
    """Save an object to the given path."""
    with Path(filename).open("wb") as f:
        # noinspection PyTypeChecker
        pickle.dump(obj, f)


def json_to_file(src, filename):
    with open(filename, "w") as f:
        json.dump(src, f, indent=4)
