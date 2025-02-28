import pandas as pd
from datasketch import MinHash, MinHashLSH
from tqdm import tqdm


def generate_hashes(
    data: pd.Series, num_perm, threshold, tokenizer, tokenizer_kwargs, use_redis
):
    if tokenizer_kwargs is None:
        tokenizer_kwargs = {}
    if use_redis:
        lsh = MinHashLSH(
            threshold=threshold,
            num_perm=num_perm,
            storage_config={
                "type": "redis",
                "redis": {"host": "localhost", "port": 6379},
            },
        )
    else:
        lsh = MinHashLSH(threshold=threshold, num_perm=num_perm)
    # Create MinHash objects for each string
    minhashes = {}
    for i, s in tqdm(data.items(), total=len(data), desc="Creating MinHash objects"):
        m = MinHash(num_perm=num_perm)
        for d in tokenizer(s, **tokenizer_kwargs):
            m.update(d.encode("utf8"))
        lsh.insert(i, m)
        minhashes[i] = m
    return lsh, minhashes


def deduplicate(
    data: pd.Series,
    threshold=0.8,
    num_perm=128,
    tokenizer=str.split,
    tokenizer_kwargs=None,
    use_redis=False,
):
    """
    Deduplicates a list of strings using MinHash and LSH, returning the indices of the duplicates.

    Args:
        data: A pandas series object containing strings.
        threshold: The Jaccard similarity threshold for deduplication.

    Returns:
        A list of integers corresponding to the duplicated values.
        :param data:  A pandas series of strings.
        :param threshold: The Jaccard similarity threshold for deduplication.
        :param num_perm: The number of permutation functions to use.
        :param tokenizer: The tokenizer function to use. Defaults to split on whitespace.
        :param tokenizer_kwargs: The keyword arguments to pass to the tokenizer.
        :param use_redis: Whether to use Redis for storage.
    """
    lsh, minhashes = generate_hashes(
        data, num_perm, threshold, tokenizer, tokenizer_kwargs, use_redis
    )

    # Identify duplicates
    duplicates = set()
    progress_bar = tqdm(data.items(), desc="Identifying duplicates (0 found)")
    for i, value in progress_bar:
        if i in duplicates:
            continue

        result = lsh.query(minhashes[i])
        for r in result:
            if r != i:
                duplicates.add(r)

        progress_bar.set_description(
            f"Identifying duplicates ({len(duplicates)} found)"
        )

    return duplicates


def deduplicate_with_collisions(
    data: pd.Series,
    threshold=0.8,
    num_perm=128,
    tokenizer=str.split,
    tokenizer_kwargs=None,
    use_redis=False,
):
    """
    Deduplicates a list of strings using MinHash and LSH return the collisions.

    Args:
        data: A list of strings.
        threshold: The Jaccard similarity threshold for deduplication.

    Returns:
        A list of integers corresponding to the duplicated values.
        :param data:  An pandas series of strings.
        :param threshold: The Jaccard similarity threshold for deduplication.
        :param num_perm: The number of permutation functions to use.
        :param tokenizer: The tokenizer function to use. Defaults to split on whitespace.
        :param tokenizer_kwargs: The keyword arguments to pass to the tokenizer.
        :param use_redis: Whether to use Redis for storage.
    """
    lsh, minhashes = generate_hashes(
        data, num_perm, threshold, tokenizer, tokenizer_kwargs, use_redis
    )

    duplicates = set()
    collisions = {}
    progress_bar = tqdm(data.items(), desc="Identifying duplicates (0 found)")
    for i, value in progress_bar:
        if i in duplicates:
            continue

        result = lsh.query(minhashes[i])
        if len(result) > 1:
            collisions[i] = []
        for r in result:
            if r != i:
                duplicates.add(r)
                collisions[i].append(r)
        progress_bar.set_description(
            f"Identifying duplicates ({len(duplicates)} found)"
        )

    return duplicates, collisions


if __name__ == "__main__":
    mock_data = [
        "This is another sentence.",
        "This is another sentence.",
        "This is a similar sentence.",
        "This is a completely different sentence.",
    ]

    duplicates_ = deduplicate(pd.Series(mock_data), threshold=0.9)
    print(duplicates_)
