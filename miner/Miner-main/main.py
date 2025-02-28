"""
    This is the main module and calls all the other modules and uses them. This module can iterate in repo list and
    within those repos can iterate in commits and calls the required functions for Maven build, Spotbugs run and others.
"""

import datetime
import glob
import json
import shutil
import os
import stat
import Tracker
from os import path
from Logger import (
    add_fix_opening,
    write_ending,
    write_opening,
    add_commit,
    Logger,
    add_project,
    set_threadsData,
)
from Git import git_fetch, git_checkout, gitRestore, close_repo, getGitDir
from Decorator import try_except, printOutput
import Maven
import Decorator
import Spotbugs
import configparser
import platform
import threading
import concurrent.futures
import ast

curr_time = datetime.datetime.now()
timestamp = curr_time.strftime("%Y%m%d_%H%M%S")
remove_dir = try_except(shutil.rmtree)
stdPrint = printOutput(print)
opsys = platform.system()
threadEnds = []
warningIDs = []
entryIDs = []
max_threads = 1
lastSuccessfulCommit = []
mine_reports = ""


@try_except
def iterate(repo_dir, spotbugs, reports, repo_list, tracker, since_date, until_date, warnings=[], entries=[]):
    """
    Iterates in repo list, calls the git_fetch function, then on the cloned repo calls the iterate_commits function
    :param repo_dir: The directory where we can clone the repos
    :param spotbugs: The location where the Spotbugs is found
    :param reports: The folder where the XML files can generated to by the Spotbugs
    :param repo_list: The list of the repos
    :param tracker: A boolean if we need running Tracker or not
    :param warnings: The list of the warnings we need to investigate
    :param entries: The list of the starting entry ID-s
    """
    if warnings and entries:
        global warningIDs, entryIDs
        warningIDs = warnings
        entryIDs = entries
    if reports == "":
        if not os.path.isdir(
            os.path.dirname(os.path.abspath(__file__)) +
            os.path.sep + "reports"
        ):
            os.mkdir(
                os.path.dirname(os.path.abspath(__file__)) +
                os.path.sep + "reports"
            )
        reports = (
            os.path.dirname(os.path.abspath(__file__))
            + os.path.sep
            + "reports"
            + os.path.sep
        )
    elif not os.path.isdir(reports):
        os.mkdir(reports)
    Logger(timestamp, reports)

    if not repo_list and not mine_reports:
        if not os.path.isdir(repo_dir):
            return
        write_opening(repo_dir.split("/")[-1])
        commits = git_fetch(0, "", [], "Project error",
                            "", "", 0, repo_dir, "", 0, since_date, until_date)
        if commits != False:
            iterate_commits("", repo_dir, commits, spotbugs, reports, tracker)
        write_ending(repo_dir.split("/")[-1])
    else:
        if repo_dir == "":
            repo_dir = (
                os.path.dirname(os.path.abspath(__file__)) +
                os.path.sep + "repo_dir"
            )
            if os.path.isdir(repo_dir):
                delete_folder(repo_dir, "", False)

            os.mkdir(repo_dir)

        for i in range(int(max_threads)):
            threadEnds.append(int(max_threads) - i - 1)

        if mine_reports:
            if not os.path.isdir(reports + "/dataset" + timestamp):
                os.mkdir(reports + "/dataset" + timestamp)
                for warning in warningIDs:
                    os.mkdir(reports + "/dataset" + timestamp + "/" + warning)
                    os.mkdir(
                        reports + "/dataset" + timestamp + "/" + warning + "/Files"
                    )
                    json = open(
                        reports
                        + "/dataset"
                        + timestamp
                        + "/"
                        + warning
                        + "/description.json",
                        "w",
                    )
                    add_fix_opening(json, warning, warningIDs)
                    json.close()
            json_reports = glob.glob(mine_reports + "/*.json")
            for file in get_last_files(reports, max_threads):
                os.remove(file)
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=int(max_threads)
            ) as executor:
                {
                    executor.submit(
                        mine_spotbugs_reports, reports, json, repo_dir, since_date, until_date
                    ): json
                    for json in json_reports
                }
            for warning in warningIDs:
                json = open(
                    reports
                    + "/dataset"
                    + timestamp
                    + "/"
                    + warning
                    + "/description.json",
                    "a",
                )
                json.write("\n    ]\n}")
                json.close()
            return

        lines = open(repo_list, "r")
        if not os.path.isdir(repo_dir) or not os.path.isfile(repo_list):
            return False

        repositories = []
        restore_repositories = {}
        files = get_last_files(reports, max_threads)
        c = len(files)
        found = False
        for line in lines:
            line = line.rstrip()
            if c == 0:
                repositories.append(line)
            else:
                line_repo_name = line.split("/")[-1].split(".")[0]
                for file in files:
                    file_repo_name = ""
                    if opsys == "Darwin":
                        splitted_file_name = file.split("/")[-1].split("_")
                    else:
                        splitted_file_name = file.split("\\")[-1].split("_")
                    ind = 1
                    while ind < len(splitted_file_name) - 2:
                        file_repo_name += splitted_file_name[ind]
                        ind += 1
                    if file_repo_name == line_repo_name:
                        restore_repositories[file] = line
                        found = True
                        c -= 1
                        break

        if not found:
            lines.seek(0)
            repositories = lines
            files = []

        for i in range(int(max_threads)):
            lastSuccessfulCommit.append("")

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=int(max_threads)
        ) as executor:
            {
                executor.submit(
                    restore,
                    file,
                    reports,
                    repo_dir,
                    spotbugs,
                    tracker,
                    restore_repositories,
                ): file
                for file in files
            }

        if not os.path.isdir(reports + "/dataset" + timestamp):
            os.mkdir(reports + "/dataset" + timestamp)
            for warning in warningIDs:
                os.mkdir(reports + "/dataset" + timestamp + "/" + warning)
                os.mkdir(reports + "/dataset" + timestamp +
                         "/" + warning + "/Files")
                json = open(
                    reports
                    + "/dataset"
                    + timestamp
                    + "/"
                    + warning
                    + "/description.json",
                    "w",
                )
                add_fix_opening(json, warning, warningIDs)
                json.close()

        with concurrent.futures.ThreadPoolExecutor(
            max_workers=int(max_threads)
        ) as executor:
            {
                executor.submit(
                    line_to_repo, line, reports, repo_dir, spotbugs, tracker, since_date, until_date
                ): line
                for line in repositories
            }
    for warning in warningIDs:
        json = open(
            reports + "/dataset" + timestamp + "/" + warning + "/description.json", "a"
        )
        json.write("\n    ]\n}")
        json.close()


def mine_spotbugs_reports(report_folder, json_report, repo_dir, since_date, until_date):
    """
    Mining without build and spotbugs run
    :param report_folder: The folder of the XML reports
    :param json_report: The JSON logging file
    :param repo_dir: The directory where we can clone the repos
    """
    c = threadEnds.pop(-1)
    global mine_reports
    threading.current_thread().name = c
    Tracker.newProject(c)
    with open(json_report, "r") as f:
        try:
            repo_link = json.load(f)[1]["project"]
        except Exception as e:
            file_text = f.read()
            json_object = file_text + "]"
            if json_object == "[]" or json_object == "]":
                threadEnds.append(c)
                return False
            repo_link = json.loads(json_object)[-1]["project"]
    link_separated = repo_link.split("/")
    repository_name = link_separated[-1].split(".")[0]
    if any(repository_name in file for file in glob.glob(report_folder + "\*.json")):
        threadEnds.append(c)
        return False
    directory = repo_dir + os.path.sep + repository_name
    repository_report_folders = glob.glob(mine_reports + "/*", recursive=False)
    repository_reports = ""
    for repository_report_folder in repository_report_folders:
        if (
            os.path.isdir(repository_report_folder)
            and repository_name in repository_report_folder
        ):
            repository_reports = repository_report_folder + "/"
    write_opening(repository_name, c)
    add_project(repo_link, c)

    xmls = glob.glob(repository_reports + "*")
    commits = git_fetch(
        str(repo_link), "", [], "Project error", "", "", c, directory, repo_link, c, since_date, until_date
    )
    if commits:
        for commit in commits:
            for report in xmls:
                if str(commit) in report:
                    if git_checkout(commit) == False:
                        continue
                    git_dir = getGitDir()
                    Tracker.parseAndCheckReports(
                        report_folder,
                        repository_reports,
                        directory,
                        repo_link,
                        commit,
                        [],
                        git_dir,
                        warningIDs,
                        entryIDs,
                        timestamp,
                    )
                    break
    threadEnds.append(c)
    write_ending(repository_name)
    close_repo()
    if os.path.isdir(directory):
        delete_folder(directory, repo_link, False)


def restore(file, reports, repo_dir, spotbugs, tracker, repolinks, since_date, until_date):
    """
    Restoring Miner after a shutdown
    :param file: The restored JSON file
    :param reports: The folder where the XML files can generated to by the Spotbugs
    :param repo_dir: The directory where we can clone the repos
    :param spotbugs: The location where the Spotbugs is found
    :param tracker: A boolean if we need running Tracker or not
    :param repolinks: The list of the repos we need to restore
    :param since_date: The date from which we want to get commits
    :param until_date: The date until which we want to get commits
    """
    repo_link, commit, time = last_run_data(file, repolinks)
    for warning in warningIDs:
        if not os.path.exists(
            reports + "/dataset" + time + "/" + warning + "/description.json"
        ):
            os.mkdir(reports + "/dataset" + time + "/" + warning)
            os.mkdir(reports + "/dataset" + time + "/" + warning + "/Files")
            json = open(
                reports + "/dataset" + time + "/" + warning + "/description.json", "w"
            )
            add_fix_opening(json, warning, warningIDs)
            json.close()
    Logger(time, reports)
    c = threadEnds.pop(-1)
    threading.current_thread().name = c
    link_separated = repo_link.split("/")
    repository_name = link_separated[len(link_separated) - 1].split(".")[0]
    directory = repo_dir + os.path.sep + repository_name
    write_opening(repository_name, c)
    add_project(str(repo_link), c)
    commits = git_fetch(
        str(repo_link), "", [], "Project error", "", "", c, directory, repo_link, c, since_date, until_date
    )
    Tracker.newProject(c)
    if (not str(commits[-1]) == commit) and (not commits == False):
        global timestamp
        timestamp = time
        report_path = (
            reports + "/" + repository_name +
            "_reports_" + str(timestamp) + os.path.sep
        )

        if commit != "first":
            set_threadsData(c, "first_write", False)
            while not str(commits[0]) == commit:
                commits.remove(commits[0])
            try:
                git_checkout(commits[0])
                git_dir = getGitDir()
                Tracker.parseAndCheckReports(
                    reports,
                    report_path,
                    repo_dir,
                    repo_link,
                    commits[0],
                    [],
                    git_dir,
                    warningIDs,
                    entryIDs,
                    timestamp,
                    False,
                )
                commits.remove(commits[0])
            except Exception as e:
                print(e)
        iterate_commits(
            reports, repo_link, directory, commits, spotbugs, report_path, tracker
        )
    threadEnds.append(c)
    write_ending(repo_link.split("/")[-1].split(".")[0])


def line_to_repo(line, reports, repo_dir, spotbugs, tracker, since_date, until_date):
    """
    Convert line from list to repo
    :param line: The line
    :param reports: The folder where the XML files can generated to by the Spotbugs
    :param repo_dir: The folder where we want to clone repo
    :param spotbugs: The location where the Spotbugs is found
    :param tracker: A boolean if we need running Tracker or not
    :param since_date: The date from which we want to get commits
    :param until_date: The date until which we want to get commits
    """
    c = threadEnds.pop(-1)
    threading.current_thread().name = c
    repo_link = line.rstrip()
    line = repo_link.split("/")
    repository_name = line[len(line) - 1].split(".")[0]
    report_path = (
        reports + "/" + repository_name +
        "_reports_" + str(timestamp) + os.path.sep
    )

    write_opening(repository_name, c)
    os.mkdir(report_path)
    directory = repo_dir + os.path.sep + repository_name
    stdPrint("", nothing=f"Working on {repository_name}")
    add_project(str(repo_link), c)
    commits = git_fetch(
        str(repo_link), "", [], "Project error", "", "", c, directory, repo_link, c, since_date, until_date
    )
    Tracker.newProject(c)
    if commits != False:
        iterate_commits(
            reports, repo_link, directory, commits, spotbugs, report_path, tracker
        )
    threadEnds.append(c)
    write_ending(repo_link.split("/")[-1].split(".")[0])


def iterate_commits(
    reports, repo_link, repo_dir, commits, spotbugs, report_path, tracker
):
    """
    Iterating in commits in a repo and running Maven, Spotbugs and Tracker
    :param repo_link: The link of the github repository
    :param repo_dir: The cloned repository we working with
    :param commits: List of commits in repo
    :param spotbugs: The location where the Spotbugs is found
    :param report_path: The directory where we can generate Spotbugs XML files
    :param tracker: A boolean if we need running Tracker or not
    """
    for i in range(len(commits)):
        try:
            if git_checkout(commits[i]) == False:
                continue
            try:
                jar_war_ear_zips = Maven.maven_build(
                    repo_dir,
                    commits,
                    i,
                    lastSuccessfulCommit[int(threading.current_thread().name)],
                )
            except Exception as e:
                add_commit(str(commits[i]), [], "build failed", str(e), "")
                lastSuccessfulCommit[int(threading.current_thread().name)] = ""
                try:
                    Maven.maven_clean(repo_dir)
                    gitRestore(repo_dir + "/pom.xml")
                except:
                    stdPrint("Restoring files failed")
                continue
            successful = False
            if jar_war_ear_zips == False:
                continue
            lastSuccessfulCommit[int(
                threading.current_thread().name)] = commits[i]
            if jar_war_ear_zips["default_build_file_path"] != "":
                if (
                    Spotbugs.run_spotbugs(
                        0,
                        str(commits[i]),
                        jar_war_ear_zips["module_build_file_list"],
                        "SB failed",
                        str(jar_war_ear_zips["default_build_file_path"]).rsplit(
                            os.path.sep, 1
                        )[1],
                        "",
                        threading.current_thread().name,
                        spotbugs,
                        report_path,
                        commits[i],
                        jar_war_ear_zips["default_build_file_path"],
                        i,
                    )
                    != False
                ):
                    if tracker == "true":
                        successful = True
                        gitRestore("pom.xml")
                        git_dir = getGitDir()
                        Tracker.parseAndCheckReports(
                            reports,
                            report_path,
                            repo_dir,
                            repo_link,
                            commits[i],
                            jar_war_ear_zips["module_build_file_list"],
                            git_dir,
                            warningIDs,
                            entryIDs,
                            timestamp,
                        )
                    else:
                        add_commit(
                            str(commits[i]),
                            jar_war_ear_zips["module_build_file_list"],
                            "successful",
                            "",
                            "",
                        )
            else:
                stdPrint("No jar, war, ear or zip file found")
                add_commit(
                    str(commits[i]),
                    jar_war_ear_zips["module_build_file_list"],
                    "SB failed",
                    "No jar, war, ear or zip file found",
                    "",
                )
            if not successful:
                gitRestore(repo_dir + "/pom.xml")
        except Exception as e:
            add_commit(str(commits[i]), [], "unknown", str(e), "")
            continue
    close_repo()
    if os.path.isdir(repo_dir):
        delete_folder(repo_dir, repo_link, False)


def get_last_files(reports, number_of_files):
    """
    Returning the JSON files we need to restore
    :param reports: The folder where the JSON files are
    :param repo_dir: The number of the files we need to restore
    :return: The JSON files
    """
    files = glob.glob(reports + "/*.json")
    files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
    return files[0: int(number_of_files)]


def last_run_data(file, repolinks):
    """
    Get data from the stopped run by JSON file
    :param file: The restored JSON file
    :param repolinks: The list of the repos we need to restore
    :return: The data of the last run
    """
    file_name = file.split(".")[-2].split("_")
    time = file_name[-2] + "_" + file_name[-1]
    try:
        with open(file, "r") as f:
            file_text = f.read()
            if file_text[-1] != "]":
                file_text += "]"
            if file_text == "[]":
                return repolinks[file], "first", time
            file_data = json.loads(file_text)
            last_commit = file_data[-1]["commit_id"]
            repo_link = file_data[-1]["project"]
            return repo_link, last_commit, time
    except Exception as e:
        print("Wrong json format in: ", file, "\n", e)
        return False


def delete_folder(directory, repo_link, last):
    """
    Deleting a folder
    :param directory: The directory we need to delete
    :param repo_link: The link of the github repository
    :param last: A boolean if it's the last repo we need to delete or not
    """
    chmod_stat = stat.S_IRWXU
    if opsys == "Windows":
        chmod_stat = stat.S_IWRITE
    for root, dirs, files in os.walk(directory):
        for dir in dirs:
            os.chmod(path.join(root, dir), chmod_stat)
        for file in files:
            os.chmod(path.join(root, file), chmod_stat)
    if last:
        remove_dir("", "", [], "last delete", "", "", 0, directory)
        return
    remove_dir(
        str(repo_link),
        "",
        [],
        "Project error",
        "Can't delete repo folder",
        "",
        0,
        directory,
    )


def main():
    """
    The main function
    """

    script_loc = os.path.dirname(os.path.abspath(__file__))

    config = configparser.ConfigParser()
    config.read(os.path.dirname(os.path.abspath(__file__)) + "/config")
    global warningIDs
    warningIDs = ast.literal_eval(config["WARNING_ID"]["warnings"])
    Decorator.output = config["ARGUMENTS"]["output"]
    Decorator.timeout = int(config["ARGUMENTS"]["timeout"])
    global entryIDs, max_threads, mine_reports
    max_threads = config["ARGUMENTS"]["threads"]
    entryIDs = ast.literal_eval(config["STARTING_ENTRY_IDS"]["entry_IDs"])
    mine_reports = config["ARGUMENTS"]["mineReports"]

    since_date = config["ARGUMENTS"]["sinceDate"].strip() if config["ARGUMENTS"]["sinceDate"].strip() else None
    until_date = config["ARGUMENTS"]["untilDate"].strip() if config["ARGUMENTS"]["untilDate"].strip() else None
    iterate(
        "",
        "",
        [],
        "Iterate failed",
        "",
        "",
        0,
        config["ARGUMENTS"]["repository"],
        config["ARGUMENTS"]["spotbugs"],
        config["ARGUMENTS"]["reports"],
        config["ARGUMENTS"]["repolist"],
        config["ARGUMENTS"]["tracker"],
        since_date,
        until_date
    )
    if config["ARGUMENTS"]["repository"] == "":
        os.chdir(script_loc)
        delete_folder(script_loc + "/repo_dir", "", True)
    print("Done.")
    return True


if __name__ == "__main__":
    main()
