# A miner tool to collect actionable and non-actionable warnings from real-life Java projects


## Description

In this project we have implemented a miner tool in Python in order to collect actionable and non-actionable warnings from Java static code analysis tool reports. We mention that it was used to obtain the the Non-Actionable Static Code Analysis Reports (NASCAR) dataset.

## Dependencies

In order to use our miner, you have to install the following softwares:
- Python 3.13.2 or newer,
- Java 23 or newer,
- PMD 7.1.0 or newer,
- Maven 3.9.9 or newer,
- Gradle 8.13 or newer,
- Spotbugs 4.9.1 or newer.


## How to Use It

1. Open a new terminal.

2. Navigate to the base directory of the miner.

3. Give execute permission to all Python scripts except `GitRemoteProgress.py`, `Project.py`, and `Transformations.py`. For this, you can type in
```bash
for script in $(ls *.py | grep -v 'GitRemoteProgress\|Project\|Transformations'); do
    chmod a+x $script
done
```

4. Install the required python packages.
```bash
python3 -m pip install docker alive_progress GitPython loguru unidiff pandas pyarrow tabulate
```

5. Run the miner as follows. 

- If you have a single git repository (e.g. `https://github.com/user/repo`), then you just type in 
```bash
./miner.py --repo-url https://github.com/user/repo --pmd --spotbugs
```
to run the full analysis. Note that you can use the usual command line arguments `--since YYYY-MM-DD` or `--until YYYY-MM-DD` if you wish
to investigate only a subset of commits.

- Moreover, you can specify a file containing a list of git repositories separated by new line characters (e.g. `repos_list.txt`). If this the case, then you can run the miner as follows:
```bash
./feeder.py --repo-list repo_list.txt --pmd --spotbugs
```
You can use the command line arguments `--since YYYY-MM-DD` or `--until YYYY-MM-DD` as before.

6. Check the collected source files as follows:
```bash
./file_checker.py
```

7. Create the `dataset.parquet` database file and the `files` directory:
```bash
./create_dataset.py
```

8. Get the different statistics in the following way:
```bash
./proj_stats.py
./pmd_stats.py
./spotbugs_stats.py
```