# FP Filtering

## Subprojects

The various subprojects in this repo.

### Miner-main

This directory contains the tool we are testing to use for TP generation.

#### How to run

First of all Miner contains python files, so you have to install python, at least version 3.
Beside python, Miner uses java, maven, Spotbugs and git. Here are the versions you should
have:

* Java version 21 or above
* Maven version 3.9.6 or above
* Spotbugs 4.8.3
* Git 2 or above 
* Python 3.8 or above + pip

Miner works on Windows and on Linux as well. There is a config file `config_default` which you should copy as `config` then you can set important arguments in `config` before running.

In the root directory, install the required python modules:

```bash
pip install -r .\requirements.txt
```

Finally, run the miner:

```bash
python main.py
```

## External

The external resources used in our work.

### **[vfdetector](https://github.com/ntgiang71096/vfdetector)**

Promising vulnerability fix finder tool. Repo: https://github.com/ntgiang71096/VFDetector

### [Related work - SOTA](https://docs.google.com/spreadsheets/d/1sPmawghIsYQKMfG4gRUYl8plXxxiZOKWNv_jPXlA4jI/edit?usp=sharing)

Google sheet containing the related work we considered.

### [Fixing commits, SA tool benchmarks, quality java repos](https://docs.google.com/spreadsheets/d/1g4YcDP2r0gDnpzm2ti8qRZNTMbEfxtcPuKzeNqPjA7A/edit?usp=sharing)

Google sheet containing all kind of miscellaneous stuff.
