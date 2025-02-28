# Deduplication with MinHash + LSH
This projects aims to be used to deduplicate the dataset "NASCAR: (Non-)Actionable Static Code Analysis Reports" dataset.

## Prerequisites
- python 3.10 or pyenv (recommended)  
- poetry

Set the required constants in `config.py`
## Install

If pyenv is installed:
```bash
pyenv install 3.10
```

```bash
poetry install
```

## Usage
```bash
pyenv local 3.10
poetry shell
python dedup_nascar.py
```
