# Set these accordingly
DATASET_PATH = "../miner/dataset.parquet"
FILES_PATH = "../miner/"

# Optional
CONTEXT_SIZE = 3
JACCARD_THRESHOLD = 0.95
N_PERM = 128

# Constants related to generated data
CACHE_ROOT = "data"
DUPLICATES_PKL = f"{CACHE_ROOT}/duplicates.pkl"
FILE_CONTENTS_PKL = f"{CACHE_ROOT}/file_contents.pkl"
FILE_CONTENTS_LABELED_PKL = f"{CACHE_ROOT}/file_contents_labeled.pkl"
COLLISIONS_JSON = f"{CACHE_ROOT}/collisions.json"
DEDUPLICATED_PATH = f"{CACHE_ROOT}/deduplicated.parquet"
