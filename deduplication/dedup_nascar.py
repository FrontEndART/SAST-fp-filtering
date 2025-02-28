"""
A script to deduplicate the NASCAR dataset using a MinHash + LSH approach.
"""

from pathlib import Path

import pandas as pd
import dask
from dask.dataframe import DataFrame
from dask import dataframe as dd
from dask.diagnostics import ProgressBar

from config import COLLISIONS_JSON
from minlsh import deduplicate, deduplicate_with_collisions
import config
from misc import process_row, process_row_labeled, load_pkl, save_pkl, json_to_file

pbar = ProgressBar()
pbar.register()
dask.config.set({"dataframe.convert-string": False})


def init_cache():
    """Initialize the cache directory."""
    Path(config.CACHE_ROOT).mkdir(exist_ok=True, parents=True)


def load_dataset(dataset_path, n_partitions=8):
    """Load the dataset from the given path."""

    print(f"Loading dataset ({dataset_path=})")
    # Setting index to False to overcome the buggy dask index reading
    return dd.read_parquet(dataset_path, index=False).repartition(
        npartitions=n_partitions
    )


# def extract_code(filepath, positions, offset=-1):
#     """Extract code parts from the file based on the given positions."""
#     with filepath.open(encoding="utf-8", errors="ignore") as file:
#         lines = file.readlines()
#         start_line = positions[0]["start_line"] + offset
#         end_line = positions[0]["end_line"] + offset
#         code_parts = (
#             res.split(r"//")[0].strip() for res in lines[start_line : end_line + 1]
#         )  # remove comments
#     return "\n".join(code_parts)


def extract_code_parts(
    ddf: DataFrame, files_root: str, force: bool = False, labeled: bool = False
) -> pd.Series:
    """Extract code parts for each entry in the dataframe."""
    print(f"Extracting code parts ({labeled=}, {files_root=})")

    if labeled:
        process_row_fn = process_row_labeled
        codes_pkl_path = Path(config.FILE_CONTENTS_LABELED_PKL)
    else:
        codes_pkl_path = Path(config.FILE_CONTENTS_PKL)
        process_row_fn = process_row

    if codes_pkl_path.exists() and not force:
        return load_pkl(codes_pkl_path)

    code_parts = ddf.apply(
        process_row_fn, axis=1, meta=pd.Series(dtype="object")
    ).compute(scheduler="processes")

    save_pkl(codes_pkl_path, code_parts)

    return code_parts


def get_duplicated_indices(code_parts):
    duplicates = deduplicate(
        code_parts,
        threshold=config.JACCARD_THRESHOLD,
        num_perm=config.N_PERM,
        use_redis=False,
    )
    save_pkl(config.DUPLICATES_PKL, duplicates)


def get_collisions(code_parts):
    duplications, collisions = deduplicate_with_collisions(
        code_parts,
        threshold=config.JACCARD_THRESHOLD,
        num_perm=config.N_PERM,
        use_redis=False,
    )

    return duplications, collisions


def map_collisions_to_code_parts(
    collisions: dict[int, list[int]], code_parts: pd.Series
):
    res = {}
    for retained, collisions in collisions.items():
        res[str((code_parts[retained], retained))] = [
            (code_parts[c], c) for c in collisions
        ]

    return res


def get_and_save_collisions(code_parts):
    """
    Get and save the collisions and duplicates.
    :param code_parts: pd.Series object of strings
    :return:
    """
    duplicates, collision_idx = get_collisions(code_parts)
    save_pkl(config.DUPLICATES_PKL, duplicates)
    collisions = map_collisions_to_code_parts(collision_idx, code_parts)
    json_to_file(collisions, COLLISIONS_JSON)


def get_and_save_deduplicates(ddf: DataFrame):
    """
    Get and save the deduplicated entries.
    :param ddf: dask.DataFrame
    :return:
    """
    pd_df = pd.DataFrame(ddf, columns=ddf.columns)
    duplicates = load_pkl(config.DUPLICATES_PKL)
    pd_df.drop(pd_df.index[sorted(duplicates)], inplace=True)
    pd_df.to_parquet(config.DEDUPLICATED_PATH)
    


def main():
    init_cache()
    ddf = load_dataset(config.DATASET_PATH)
    code_parts = extract_code_parts(ddf, config.FILES_PATH, labeled=True)
    get_and_save_collisions(code_parts)
    get_and_save_deduplicates(ddf)
    pass


if __name__ == "__main__":
    main()
