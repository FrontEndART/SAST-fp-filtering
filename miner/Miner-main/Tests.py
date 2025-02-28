"""
This module contains tests for functions
"""

from genericpath import isdir
from unittest.case import _AssertRaisesContext
from Parser import find_file, parse_xml
from Tracker import parseAndCheckReports, newProject
from Decorator import try_except, print_command
import unittest
from unittest.mock import MagicMock, patch
import Decorator
import subprocess
import Spotbugs
import Maven
import os
import git
import main
import Git
import Tracker
from main import delete_folder, iterate, last_run_data
import os.path
import configparser
import datetime
import multiprocessing
import time
import json
import glob
import threading

warning_ids = ["EI_EXPOSE_REP", "EI_EXPOSE_REP2", "FI_PUBLIC_SHOULD_BE_PROTECTED", "MS_EXPOSE_REP", "MS_MUTABLE_ARRAY",
               "MS_MUTABLE_COLLECTION", "MS_MUTABLE_COLLECTION_PKGPROTECT", "MS_SHOULD_BE_FINAL",
               "NP_NULL_ON_SOME_PATH", "NP_NULL_ON_SOME_PATH_EXCEPTION", "NP_NULL_PARAM_DEREF",
               "NP_NULL_PARAM_DEREF_ALL_TARGETS_DANGEROUS", "NP_NULL_PARAM_DEREF_NONVIRTUAL",
               "SQL_NONCONSTANT_STRING_PASSED_TO_EXECUTE", "XSS_REQUEST_PARAMETER_TO_SERVLET_WRITER", ]
entry_ids = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]


def test_cloning(mocker):
    mocker.patch("Logger.add_commit")
    mocker.patch("Logger.add_project")
    os.chdir("testInput")
    assert Git.git_clone(
        "https://github.com/searchlabltd/Miner", os.path.dirname(
            os.path.abspath(__file__)) + "/testInput/Miner",
        0) == False, "Should be false"
    assert Git.git_clone(
        "https://github.com/tokker/commitYearTest",
        os.path.dirname(os.path.abspath(__file__)) + "/testInput/commitYearTest", 1) == None, "Should be successful"
    assert Git.git_clone(
        "https://github.com/RustyPincer/TestRepo", os.path.dirname(
            os.path.abspath(__file__)) + "/testInput/TestRepo",
        2) == None, "Should be successful"


def test_gitFetch(mocker):
    mocker.patch("Git.git_clone", return_value=False)
    assert Git.git_fetch("", "", "", "", "", "", 0, "",
                         "foo", 0) == False, "Should return False"
    mocker.patch("Git.git_clone", return_value=True)
    assert len(Git.git_fetch("https://github.com/RustyPincer/TestRepo", "", [], "", "", "", 0, os.path.dirname(
        os.path.abspath(__file__)) + "/testInput/TestRepo", "https://github.com/RustyPincer/TestRepo",
        0)) == 22, "Should be the same"


def test_wrong_config_input(mocker):
    mocker.patch("Logger.add_project")
    config = configparser.ConfigParser()
    config.read(os.path.dirname(os.path.abspath(__file__)) +
                "/testInput/config_test/config")
    assert iterate("", "", [], "Iterate failed", "", "", 0, config["ARGUMENTS"]["repository"],
                   config["ARGUMENTS"]["spotbugs"],
                   config['ARGUMENTS']['reports'], config['ARGUMENTS']['repolist'],
                   config['ARGUMENTS']['tracker']) == False, "Should return False"


def test_right_config_input():
    config = configparser.ConfigParser()
    config.read(os.path.dirname(os.path.abspath(__file__)) +
                "/testInput/config_test/config_right")
    assert iterate(0, "", [], "Iterate failed", "", "", "", config['ARGUMENTS']['repository'],
                   config['ARGUMENTS']['spotbugs'],
                   config['ARGUMENTS']['reports'],
                   os.path.dirname(os.path.abspath(__file__)) +
                   config['ARGUMENTS']['repolist'],
                   config['ARGUMENTS']['tracker']) == None, "Should return None"


def test_right_config_input_repository():
    os.chdir(os.path.dirname(
        os.path.abspath(__file__)) + "/testInput/config_test")
    assert Git.git_clone(
        "https://github.com/RustyPincer/OneCommitRepo",
        os.path.dirname(os.path.abspath(__file__)) + "/testInput/OneCommitRepo", 3) == None, "Should be successful"
    os.chdir("..")
    config = configparser.ConfigParser()
    config.read(os.path.dirname(os.path.abspath(__file__)) +
                "/testInput/config_test/config_right_repo")
    assert iterate(0, "", [], "Iterate failed", "", "", "",
                   os.path.dirname(os.path.abspath(__file__)) +
                   config['ARGUMENTS']['repository'],
                   config['ARGUMENTS']['spotbugs'],
                   config['ARGUMENTS']['reports'], config['ARGUMENTS']['repolist'],
                   config['ARGUMENTS']['tracker']) == None, "Should return None"


def test_try_except_wrapper(mocker):
    mocker.patch("Logger.add_commit")

    def raiseException():
        raise Exception("exception")

    method = try_except(raiseException)
    assert method(0, "", [], "", "", "", 0) == False, "Should return False"


def test_performance():
    delete_folder(os.path.dirname(os.path.abspath(__file__)) +
                  "/reports", "", "")
    start_time = datetime.datetime.now()
    repo_list = str(os.path.dirname(os.path.abspath(
        __file__)) + "/testInput/repo_list.txt")
    value = iterate('', '', [], '', '', '', 0, "", "", "", repo_list, 'true')
    end_time = datetime.datetime.now()
    execution_time = end_time - start_time
    assert int(execution_time.seconds) < 500


def test_report_mine(mocker):
    mocker.patch.object(main, "warningIDs", warning_ids)
    mocker.patch.object(main, "entryIDs", [
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    mocker.patch.object(main, "mine_reports", str(
        os.path.dirname(os.path.abspath(__file__)) + "/reports"))
    mocker.patch.object(main, "timestamp",
                        datetime.datetime.now().strftime("%Y%m%d_%H%M%S"))
    repo_list = str(os.path.dirname(os.path.abspath(
        __file__)) + "/testInput/repo_list.txt")
    reports = str(os.path.dirname(os.path.abspath(
        __file__)) + "/reports2")
    iterate('', '', [], '', '', '', 0, "", "", reports, repo_list, 'true')

    with open(str(os.path.dirname(os.path.abspath(__file__)) + "/testInput/report_mine/report_mine.json")) as f:
        example = json.load(f)
    files = glob.glob(
        str(os.path.dirname(os.path.abspath(__file__)) + "/reports2/*.json"))
    print(files)
    with open(files[0]) as f:
        current = json.load(f)
    assert example == current


def test_performance_multithread(mocker):
    mocker.patch.object(main, "max_threads", 2)
    start_time = datetime.datetime.now()
    repo_list = str(os.path.dirname(os.path.abspath(
        __file__)) + "/testInput/repo_list2.txt")
    value = iterate('', '', [], '', '', '', 0, "", "", "", repo_list, 'true')
    end_time = datetime.datetime.now()
    execution_time = end_time - start_time
    assert int(execution_time.seconds) < 1500


def test_restore(mocker):
    delete_folder(os.path.dirname(os.path.abspath(__file__)) +
                  "/reports", "", "")
    mocker.patch.object(main, "warningIDs", warning_ids)
    mocker.patch.object(main, "entryIDs", [
                        0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0])
    repo_list = str(os.path.dirname(os.path.abspath(
        __file__)) + "/testInput/repo_list.txt")
    proc = multiprocessing.Process(target=iterate, args=(
        '', '', [], '', '', '', 0, "", "", "", repo_list, 'true', warning_ids,
        [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]))
    proc.start()
    time.sleep(50)
    proc.terminate()
    time.sleep(2)
    t = threading.Thread(target=iterate, args=(
        '', '', [], '', '', '', 0, str(os.path.dirname(os.path.abspath(__file__))), "", "", repo_list, 'true'))
    t.start()
    t.join()
    example = {}
    current = {}
    with open(str(os.path.dirname(os.path.abspath(__file__)) + "/testInput/test_restore/example.json")) as f:
        example = json.load(f)
    files = glob.glob(
        str(os.path.dirname(os.path.abspath(__file__)) + "/reports/*.json"))
    with open(files[0]) as f:
        current = json.load(f)
    assert example == current


def test_restore_empty_json():
    file = str(os.path.dirname(os.path.abspath(__file__)) +
               "/testInput/test_restore/empty.json")
    _, commit, _ = last_run_data(file, {file: ""})
    assert commit == "first", "Should be first"


def test_methods_during_run(mocker):
    if not os.path.isdir(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports"):
        os.mkdir(os.path.dirname(os.path.abspath(
            __file__)) + "/testInput/reports")
    mocker.patch("Logger.add_commit")
    mocker.patch("Logger.add_fix")
    mocker.patch("Git.getCurrentRepo", return_value="0")
    mocker.patch("Tracker.getCurrentThread", return_value="0")
    mocker.patch.object(Git, "repo_path", [
        {'thread_id': '0', 'path': os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo"}])
    git_dir = git.Git(os.path.dirname(
        os.path.abspath(__file__)) + "/testInput/TestRepo")
    os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo")
    assert Git.git_checkout(
        "9c60a3113feb1c0baaafbb3e3da3efdf7c03c008") == None, "Should be equal"
    assert Maven.commitFilter(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", [
        "9c60a3113feb1c0baaafbb3e3da3efdf7c03c008", "480a7f197df236090a6ed49b473cd79d8651128e"],
        0) == True, "Should return True"
    mocker.patch("Maven.commitFilter", return_value=True)
    assert Maven.maven_build(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo",
                             ["9c60a3113feb1c0baaafbb3e3da3efdf7c03c008",
                                 "480a7f197df236090a6ed49b473cd79d8651128e"],
                             0)[
        "default_build_file_path"] == os.path.dirname(os.path.abspath(
            __file__)) + "/testInput/TestRepo" + os.path.sep + "target" + os.path.sep + "my_app-0.0.1-SNAPSHOT.jar", "Should be the same"
    assert Spotbugs.run_spotbugs("", "", [], "", "", "", "", "",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/reports/",
                                 "9c60a3113feb1c0baaafbb3e3da3efdf7c03c008",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/TestRepo/target/my_app-0.0.1-SNAPSHOT.jar",
                                 0) == None, "Should return None"
    newProject(0)
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "9c60a3113feb1c0baaafbb3e3da3efdf7c03c008",
                                [], git_dir, warning_ids, entry_ids, 0) == -1, "Should return -1"


def test_tracker_no_reports(mocker):
    mocker.patch("Tracker.listdir", return_value=[])
    mocker.patch("Logger.add_commit")
    mocker.patch.object(Tracker, "threadsData", {'MainThread':
                                                 {'newCommitParsed': {'commit_id': '', 'warnings': []}, 'originCommitParsed': {'commit_id': '', 'warnings': []}, 'projectFixes': [], 'fixes': []}})
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "9c60a3113feb1c0baaafbb3e3da3efdf7c03c008",
                                [], "", warning_ids, entry_ids, 0) == 0, "Should return 0"


def test_tracker_no_matching_report(mocker):
    mocker.patch("Tracker.listdir", return_value=["a", "b"])
    mocker.patch("Logger.add_commit")
    mocker.patch.object(Tracker, "threadsData", {'MainThread':
                                                 {'newCommitParsed': {'commit_id': '', 'warnings': []}, 'originCommitParsed': {'commit_id': '', 'warnings': []}, 'projectFixes': [], 'fixes': []}})
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "9c60a3113feb1c0baaafbb3e3da3efdf7c03c008",
                                [], "", warning_ids, entry_ids, 0) == 0, "Should return 0"


def test_tracker_missing_thread_in_threadsdata(mocker):
    mocker.patch("Tracker.listdir", return_value=["a", "b"])
    mocker.patch("Logger.add_commit")
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "a",
                                [], "", warning_ids, entry_ids, 0) == None, "Should return None"


def test_tracker_parser_exception(mocker):
    mocker.patch('Parser.parse_xml', side_effect=Exception("ERROR!"))
    mocker.patch("Tracker.listdir", return_value=["a", "b"])
    mocker.patch("Logger.add_commit")
    mocker.patch.object(Tracker, "threadsData", {'MainThread':
                                                 {'newCommitParsed': {'commit_id': '', 'warnings': []}, 'originCommitParsed': {'commit_id': '', 'warnings': []}, 'projectFixes': [], 'fixes': []}})
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "a",
                                [], "", warning_ids, entry_ids, 0) == None, "Should return None"


def test_tracker_diffOfCommits_exception(mocker):
    mocker.patch('Tracker.diffOfCommits', side_effect=Exception("ERROR!"))
    mocker.patch("Tracker.listdir", return_value=["a", "b"])
    mocker.patch("Logger.add_commit")
    mocker.patch.object(Tracker, "threadsData", {'MainThread':
                                                 {'newCommitParsed': {'commit_id': '', 'warnings': []}, 'originCommitParsed': {'commit_id': '', 'warnings': []}, 'projectFixes': [], 'fixes': []}})
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "a",
                                [], "", warning_ids, entry_ids, 0) == None, "Should return None"


def test_gitDiff_exception(mocker):
    mocker.patch('Tracker.gitDiff', side_effect=Exception("ERROR!"))
    mocker.patch("Tracker.listdir", return_value=["a", "b"])
    mocker.patch("Logger.add_commit")
    mocker.patch.object(Tracker, "threadsData", {'MainThread': {'newCommitParsed': {'commit_id': 'b', 'warnings': []}, 'originCommitParsed': {
                        'commit_id': 'a', 'warnings': [{"new_location": {"file": "f", "startLineNumber": 1, "endLineNumber": 2}}]}, 'projectFixes': [], 'fixes': []}})
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "a",
                                [], "", warning_ids, entry_ids, 0) == None, "Should return None"


def test_gitDiff_False(mocker):
    mocker.patch('Tracker.gitDiff', return_value=False)
    mocker.patch("Tracker.listdir", return_value=["a", "b"])
    mocker.patch("Logger.add_commit")
    mocker.patch.object(Tracker, "threadsData", {'MainThread': {'newCommitParsed': {'commit_id': 'b', 'warnings': []}, 'originCommitParsed': {
                        'commit_id': 'a', 'warnings': [{"new_location": {"file": "f", "startLineNumber": 1, "endLineNumber": 2}}]}, 'projectFixes': [], 'fixes': []}})
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "a",
                                [], "", warning_ids, entry_ids, 0) == 0, "Should return 0"


def test_gitDiff_returns(mocker):
    mocker.patch('Tracker.gitDiff', return_value=[3])
    mocker.patch("Tracker.listdir", return_value=["a", "b"])
    mocker.patch("Logger.add_commit")
    mocker.patch("Logger.add_fix")
    mocker.patch.object(Tracker, "threadsData", {'MainThread': {'newCommitParsed': {'commit_id': 'b', 'warnings': [{"new_location": {"file": "f", "startLineNumber": 1, "endLineNumber": 2}}]}, 'originCommitParsed': {
                        'commit_id': 'a', 'warnings': [{"new_location": {"file": "f", "startLineNumber": 1, "endLineNumber": 2}, "origin_location": {}, "warning_name": "w"}]}, 'projectFixes': [], 'fixes': []}})
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "a",
                                [], "", warning_ids, entry_ids, 0) == 1, "Should return 1"


def test_gitDiff_returns_but_not_a_fix(mocker):
    mocker.patch('Tracker.diffOfCommits')
    mocker.patch('Parser.parse_xml', return_value=[
                 {"location": "1-2", "warning_id": "w", "file": "f"}])
    mocker.patch('Tracker.identifyWarning', return_value={"new_location": {
                 "file": "f", "startLineNumber": 1, "endLineNumber": 1}})
    mocker.patch('Tracker.gitDiff', return_value=[1])
    mocker.patch("Tracker.listdir", return_value=["a", "b"])
    mocker.patch("Logger.add_commit")
    mocker.patch("Logger.add_fix")
    mocker.patch.object(Tracker, "threadsData", {'MainThread': {'newCommitParsed': {'commit_id': 'b', 'warnings': [{"new_location": {"file": "f", "startLineNumber": 1, "endLineNumber": 1}}]}, 'originCommitParsed': {
                        'commit_id': 'a', 'warnings': [{"new_location": {"file": "f", "startLineNumber": 1, "endLineNumber": 2}, "origin_location": {}, "warning_name": "w"}]}, 'projectFixes': [], 'fixes': []}})
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "a",
                                [], "", warning_ids, entry_ids, 0) == 0, "Should return 0"


def test_identifyWarning_exception(mocker):
    mocker.patch('Parser.parse_xml', return_value=[
                 {"location": "1-2", "warning_id": "w", "file": "f"}])
    mocker.patch('Tracker.identifyWarning', side_effect=Exception("ERROR!"))
    mocker.patch("Tracker.listdir", return_value=["a", "b"])
    mocker.patch("Logger.add_commit")
    mocker.patch.object(Tracker, "threadsData", {'MainThread': {'newCommitParsed': {'commit_id': 'b', 'warnings': [{"new_location": {"file": "f", "startLineNumber": 1, "endLineNumber": 1}}]}, 'originCommitParsed': {
                        'commit_id': 'a', 'warnings': [{"new_location": {"file": "f", "startLineNumber": 1, "endLineNumber": 2}, "origin_location": {}, "warning_name": "w"}]}, 'projectFixes': [], 'fixes': []}})
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "a",
                                [], "", warning_ids, entry_ids, 0) == None, "Should return None"


def test_Fix_and_no_current_warnings(mocker):
    mocker.patch("Logger.add_commit")
    mocker.patch("Logger.add_fix")
    mocker.patch("Git.getCurrentRepo", return_value="0")
    mocker.patch("Tracker.getCurrentThread", return_value="0")
    mocker.patch.object(Git, "repo_path", [
        {'thread_id': '0', 'path': os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo"}])
    git_dir = git.Git(os.path.dirname(
        os.path.abspath(__file__)) + "/testInput/TestRepo")
    assert Git.git_checkout(
        "480a7f197df236090a6ed49b473cd79d8651128e") == None, "Should be equal"
    mocker.patch("Maven.detect_changes", return_value=True)
    assert Maven.commitFilter(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", [
        "9c60a3113feb1c0baaafbb3e3da3efdf7c03c008", "480a7f197df236090a6ed49b473cd79d8651128e"],
        1) == True, "Should return True"
    mocker.patch("Maven.commitFilter", return_value=True)
    assert Maven.maven_build(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo",
                             ["9c60a3113feb1c0baaafbb3e3da3efdf7c03c008",
                                 "480a7f197df236090a6ed49b473cd79d8651128e"],
                             1)[
        "default_build_file_path"] == os.path.dirname(os.path.abspath(
            __file__)) + "/testInput/TestRepo" + os.path.sep + "target" + os.path.sep + "my_app-0.0.1-SNAPSHOT.jar", "Should be the same"
    assert Spotbugs.run_spotbugs(0, "", [], "", "", "", "", "",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/reports/",
                                 "480a7f197df236090a6ed49b473cd79d8651128e",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/TestRepo/target/my_app-0.0.1-SNAPSHOT.jar",
                                 0) == None, "Should return None"
    warnings = parse_xml(os.path.dirname(os.path.abspath(
        __file__)) + "/testInput/reports/spotbugs_report__00_480a7f197df236090a6ed49b473cd79d8651128e_my_app-0.0.1-SNAPSHOT.xml",
        os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", warning_ids)
    assert len(warnings) == 0, "Should be equal"
    mocker.patch("Parser.parse_xml", return_value=warnings)
    mocker.patch.object(Tracker, "threadsData", {'0': {'newCommitParsed': {}, 'originCommitParsed': {
        'commit_id': '9c60a3113feb1c0baaafbb3e3da3efdf7c03c008', 'warnings': [{'origin_location': {
            'commit_id': '^9c60a31', 'file': 'src/main/java/my_app/Main.java', 'startLineNumber': 4,
            'endLineNumber': 4},
            'new_location': {'file': 'src/main/java/my_app/Main.java', 'startLineNumber': '4', 'endLineNumber': '4'},
            'warning_name': 'MS_SHOULD_BE_FINAL'}]}, 'projectFixes': [], 'fixes': []}})
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "480a7f197df236090a6ed49b473cd79d8651128e",
                                [], git_dir, warning_ids, entry_ids, 0) == 1, "Should be equal"


def test_warningAppear_with_other_changes(mocker):
    mocker.patch("Logger.add_commit")
    mocker.patch("Logger.add_fix")
    mocker.patch("Git.getCurrentRepo", return_value="0")
    mocker.patch("Tracker.getCurrentThread", return_value="0")
    mocker.patch.object(Git, "repo_path", [
        {'thread_id': '0', 'path': os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo"}])
    git_dir = git.Git(os.path.dirname(
        os.path.abspath(__file__)) + "/testInput/TestRepo")
    assert Git.git_checkout(
        "eaf1489478e45330c6779e9a71d3cf65469b9f6f") == None, "Should be equal"
    mocker.patch("Maven.detect_changes", return_value=True)
    assert Maven.commitFilter(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", [
        "", "480a7f197df236090a6ed49b473cd79d8651128e", "eaf1489478e45330c6779e9a71d3cf65469b9f6f"],
        2) == True, "Should return True"
    mocker.patch("Maven.commitFilter", return_value=True)
    assert Maven.maven_build(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo",
                             ["", "480a7f197df236090a6ed49b473cd79d8651128e",
                              "eaf1489478e45330c6779e9a71d3cf65469b9f6f"], 2)[
        "default_build_file_path"] == os.path.dirname(os.path.abspath(
            __file__)) + "/testInput/TestRepo" + os.path.sep + "target" + os.path.sep + "my_app-0.0.1-SNAPSHOT.jar", "Should be the same"
    assert Spotbugs.run_spotbugs(0, "", [], "", "", "", "", "",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/reports/",
                                 "eaf1489478e45330c6779e9a71d3cf65469b9f6f",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/TestRepo/target/my_app-0.0.1-SNAPSHOT.jar",
                                 0) == None, "Should return None"
    warnings = parse_xml(os.path.dirname(os.path.abspath(
        __file__)) + "/testInput/reports/spotbugs_report__00_eaf1489478e45330c6779e9a71d3cf65469b9f6f_my_app-0.0.1-SNAPSHOT.xml",
        os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", warning_ids)
    assert len(warnings) == 1, "Should be equal"
    mocker.patch("Parser.parse_xml", return_value=warnings)
    mocker.patch.object(Tracker, "threadsData", {'0': {'newCommitParsed': {}, 'originCommitParsed': {
        'commit_id': '480a7f197df236090a6ed49b473cd79d8651128e', 'warnings': []}, 'projectFixes': [], 'fixes': []}})
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "eaf1489478e45330c6779e9a71d3cf65469b9f6f",
                                [], git_dir, warning_ids, entry_ids, 0) == 0, "Should be equal"


def test_moving_warning(mocker):
    mocker.patch("Logger.add_commit")
    mocker.patch("Logger.add_fix")
    mocker.patch("Git.getCurrentRepo", return_value="0")
    mocker.patch("Tracker.getCurrentThread", return_value="0")
    mocker.patch.object(Git, "repo_path", [
        {'thread_id': '0', 'path': os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo"}])
    git_dir = git.Git(os.path.dirname(
        os.path.abspath(__file__)) + "/testInput/TestRepo")
    assert Git.git_checkout(
        "6367faae527cd90033e081487df89d53b065b1ee") == None, "Should be equal"
    mocker.patch("Maven.detect_changes", return_value=True)
    assert Maven.commitFilter(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", [
        "", "", "eaf1489478e45330c6779e9a71d3cf65469b9f6f", "6367faae527cd90033e081487df89d53b065b1ee"],
        3) == True, "Should return True"
    mocker.patch("Maven.commitFilter", return_value=True)
    assert Maven.maven_build(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo",
                             ["", "", "eaf1489478e45330c6779e9a71d3cf65469b9f6f",
                              "6367faae527cd90033e081487df89d53b065b1ee"], 3)[
        "default_build_file_path"] == os.path.dirname(os.path.abspath(
            __file__)) + "/testInput/TestRepo" + os.path.sep + "target" + os.path.sep + "my_app-0.0.1-SNAPSHOT.jar", "Should be the same"
    assert Spotbugs.run_spotbugs(0, "", [], "", "", "", "", "",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/reports/",
                                 "6367faae527cd90033e081487df89d53b065b1ee",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/TestRepo/target/my_app-0.0.1-SNAPSHOT.jar",
                                 0) == None, "Should return None"
    warnings = parse_xml(os.path.dirname(os.path.abspath(
        __file__)) + "/testInput/reports/spotbugs_report__00_6367faae527cd90033e081487df89d53b065b1ee_my_app-0.0.1-SNAPSHOT.xml",
        os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", warning_ids)
    assert len(warnings) == 1, "Should be equal"
    mocker.patch("Parser.parse_xml", return_value=warnings)
    mocker.patch.object(Tracker, "threadsData", {'0': {'newCommitParsed': {}, 'originCommitParsed': {
        'commit_id': 'eaf1489478e45330c6779e9a71d3cf65469b9f6f', 'warnings': [{'origin_location': {
            'commit_id': 'eaf14894', 'file': 'src/main/java/my_app/Main.java', 'startLineNumber': 5,
            'endLineNumber': 5}, 'new_location': {'file': 'src/main/java/my_app/Main.java', 'startLineNumber': '5',
                                                  'endLineNumber': '5'}, 'warning_name': 'MS_SHOULD_BE_FINAL'}]},
        'projectFixes': [], 'fixes': []}})
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "6367faae527cd90033e081487df89d53b065b1ee",
                                [], git_dir, warning_ids, entry_ids, 0) == 0, "Should be equal"


def test_changing_places_of_two_warnings(mocker):
    mocker.patch("Logger.add_commit")
    mocker.patch("Logger.add_fix")
    mocker.patch("Git.getCurrentRepo", return_value="0")
    mocker.patch("Tracker.getCurrentThread", return_value="0")
    mocker.patch.object(Git, "repo_path", [
        {'thread_id': '0', 'path': os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo"}])
    git_dir = git.Git(os.path.dirname(
        os.path.abspath(__file__)) + "/testInput/TestRepo")
    assert Git.git_checkout(
        "11f4750b2330c80369c3c91fed6691c902cb7506") == None, "Should be equal"
    mocker.patch("Maven.detect_changes", return_value=True)
    assert Maven.commitFilter(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", [
        "", "", "", "", "a63b5277900620b1c94e68563a8963081bb77911", "11f4750b2330c80369c3c91fed6691c902cb7506"],
        5) == True, "Should return True"
    mocker.patch("Maven.commitFilter", return_value=True)
    assert Maven.maven_build(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo",
                             ["", "", "", "", "a63b5277900620b1c94e68563a8963081bb77911",
                              "11f4750b2330c80369c3c91fed6691c902cb7506"], 5)[
        "default_build_file_path"] == os.path.dirname(os.path.abspath(
            __file__)) + "/testInput/TestRepo" + os.path.sep + "target" + os.path.sep + "my_app-0.0.1-SNAPSHOT.jar", "Should be the same"
    assert Spotbugs.run_spotbugs(0, "", [], "", "", "", "", "",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/reports/",
                                 "11f4750b2330c80369c3c91fed6691c902cb7506",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/TestRepo/target/my_app-0.0.1-SNAPSHOT.jar",
                                 0) == None, "Should return None"
    warnings = parse_xml(os.path.dirname(os.path.abspath(
        __file__)) + "/testInput/reports/spotbugs_report__00_11f4750b2330c80369c3c91fed6691c902cb7506_my_app-0.0.1-SNAPSHOT.xml",
        os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", warning_ids)
    assert len(warnings) == 2, "Should be equal"
    mocker.patch("Parser.parse_xml", return_value=warnings)
    mocker.patch.object(Tracker, "threadsData", {'0': {'newCommitParsed': {}, 'originCommitParsed': {
        "commit_id": "a63b5277900620b1c94e68563a8963081bb77911", "warnings": [{"origin_location": {
            "commit_id": "a63b5277", "file": "src/main/java/my_app/Main.java", "startLineNumber": 6,
            "endLineNumber": 6}, "new_location": {"file": "src/main/java/my_app/Main.java", "startLineNumber": "6",
                                                  "endLineNumber": "6"}, "warning_name": "MS_SHOULD_BE_FINAL"}, {
            "origin_location": {
                "commit_id": "eaf14894",
                "file": "src/main/java/my_app/Main.java",
                "startLineNumber": 5,
                "endLineNumber": 5},
            "new_location": {
                "file": "src/main/java/my_app/Main.java",
                "startLineNumber": "4",
                "endLineNumber": "4"},
            "warning_name": "MS_SHOULD_BE_FINAL"}]},
        'projectFixes': [], 'fixes': []}})
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "11f4750b2330c80369c3c91fed6691c902cb7506",
                                [], git_dir, warning_ids, entry_ids, 0) == 0, "Should be equal"


def test_modifying_line_not_fixing_warning(mocker):
    mocker.patch("Logger.add_commit")
    mocker.patch("Logger.add_fix")
    mocker.patch("Git.getCurrentRepo", return_value="0")
    mocker.patch("Tracker.getCurrentThread", return_value="0")
    mocker.patch.object(Git, "repo_path", [
        {'thread_id': '0', 'path': os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo"}])
    git_dir = git.Git(os.path.dirname(
        os.path.abspath(__file__)) + "/testInput/TestRepo")
    assert Git.git_checkout(
        "9e7aff6b84c90109aacb940b33ee99b085f4be63") == None, "Should be equal"
    mocker.patch("Maven.detect_changes", return_value=True)
    assert Maven.commitFilter(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", [
        "", "", "", "", "", "11f4750b2330c80369c3c91fed6691c902cb7506", "9e7aff6b84c90109aacb940b33ee99b085f4be63"],
        6) == True, "Should return True"
    mocker.patch("Maven.commitFilter", return_value=True)
    assert Maven.maven_build(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo",
                             ["", "", "", "", "", "11f4750b2330c80369c3c91fed6691c902cb7506",
                              "9e7aff6b84c90109aacb940b33ee99b085f4be63"], 6)[
        "default_build_file_path"] == os.path.dirname(os.path.abspath(
            __file__)) + "/testInput/TestRepo" + os.path.sep + "target" + os.path.sep + "my_app-0.0.1-SNAPSHOT.jar", "Should be the same"
    assert Spotbugs.run_spotbugs(0, "", [], "", "", "", "", "",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/reports/",
                                 "9e7aff6b84c90109aacb940b33ee99b085f4be63",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/TestRepo/target/my_app-0.0.1-SNAPSHOT.jar",
                                 0) == None, "Should return None"
    warnings = parse_xml(os.path.dirname(os.path.abspath(
        __file__)) + "/testInput/reports/spotbugs_report__00_9e7aff6b84c90109aacb940b33ee99b085f4be63_my_app-0.0.1-SNAPSHOT.xml",
        os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", warning_ids)
    assert len(warnings) == 2, "Should be equal"
    mocker.patch("Parser.parse_xml", return_value=warnings)
    mocker.patch.object(Tracker, "threadsData", {'0': {'newCommitParsed': {}, 'originCommitParsed': {
        "commit_id": '11f4750b2330c80369c3c91fed6691c902cb7506', "warnings": [{'origin_location': {
            'commit_id': 'a63b5277', 'file': 'src/main/java/my_app/Main.java', 'startLineNumber': 6,
            'endLineNumber': 6}, 'new_location': {'file': 'src/main/java/my_app/Main.java', 'startLineNumber': '4',
                                                  'endLineNumber': '4'}, 'warning_name': 'MS_SHOULD_BE_FINAL'}, {
            'origin_location': {
                'commit_id': 'eaf14894',
                'file': 'src/main/java/my_app/Main.java',
                'startLineNumber': 5,
                'endLineNumber': 5},
            'new_location': {
                'file': 'src/main/java/my_app/Main.java',
                'startLineNumber': '6',
                'endLineNumber': '6'},
            'warning_name': 'MS_SHOULD_BE_FINAL'}]},
        'projectFixes': [], 'fixes': []}})
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "9e7aff6b84c90109aacb940b33ee99b085f4be63",
                                [], git_dir, warning_ids, entry_ids, 0) == 0, "Should be equal"


def test_fixingOne_movingAnother_warning(mocker):
    mocker.patch("Logger.add_commit")
    mocker.patch("Logger.add_fix")
    mocker.patch("Git.getCurrentRepo", return_value="0")
    mocker.patch("Tracker.getCurrentThread", return_value="0")
    mocker.patch.object(Git, "repo_path", [
        {'thread_id': '0', 'path': os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo"}])
    git_dir = git.Git(os.path.dirname(
        os.path.abspath(__file__)) + "/testInput/TestRepo")
    assert Git.git_checkout(
        "7ad2954ad5eabb8adf853b9c6be00f208bcc115e") == None, "Should be equal"
    mocker.patch("Maven.detect_changes", return_value=True)
    assert Maven.commitFilter(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", [
        "", "", "", "", "", "", "9e7aff6b84c90109aacb940b33ee99b085f4be63", "7ad2954ad5eabb8adf853b9c6be00f208bcc115e"],
        7) == True, "Should return True"
    mocker.patch("Maven.commitFilter", return_value=True)
    assert Maven.maven_build(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo",
                             ["", "", "", "", "", "", "9e7aff6b84c90109aacb940b33ee99b085f4be63",
                              "7ad2954ad5eabb8adf853b9c6be00f208bcc115e"], 7)[
        "default_build_file_path"] == os.path.dirname(os.path.abspath(
            __file__)) + "/testInput/TestRepo" + os.path.sep + "target" + os.path.sep + "my_app-0.0.1-SNAPSHOT.jar", "Should be the same"
    assert Spotbugs.run_spotbugs(0, "", [], "", "", "", "", "",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/reports/",
                                 "7ad2954ad5eabb8adf853b9c6be00f208bcc115e",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/TestRepo/target/my_app-0.0.1-SNAPSHOT.jar",
                                 0) == None, "Should return None"
    warnings = parse_xml(os.path.dirname(os.path.abspath(
        __file__)) + "/testInput/reports/spotbugs_report__00_7ad2954ad5eabb8adf853b9c6be00f208bcc115e_my_app-0.0.1-SNAPSHOT.xml",
        os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", warning_ids)
    assert len(warnings) == 1, "Should be equal"
    mocker.patch("Parser.parse_xml", return_value=warnings)
    mocker.patch.object(Tracker, "threadsData", {'0': {'newCommitParsed': {}, 'originCommitParsed': {
        "commit_id": '9e7aff6b84c90109aacb940b33ee99b085f4be63', "warnings": [{'origin_location': {
            'commit_id': '9e7aff6b', 'file': 'src/main/java/my_app/Main.java', 'startLineNumber': 4,
            'endLineNumber': 4}, 'new_location': {'file': 'src/main/java/my_app/Main.java', 'startLineNumber': '4',
                                                  'endLineNumber': '4'}, 'warning_name': 'MS_SHOULD_BE_FINAL'}, {
            'origin_location': {
                'commit_id': 'eaf14894',
                'file': 'src/main/java/my_app/Main.java',
                'startLineNumber': 5,
                'endLineNumber': 5},
            'new_location': {
                'file': 'src/main/java/my_app/Main.java',
                'startLineNumber': '6',
                'endLineNumber': '6'},
            'warning_name': 'MS_SHOULD_BE_FINAL'}]},
        'projectFixes': [], 'fixes': []}})
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "7ad2954ad5eabb8adf853b9c6be00f208bcc115e",
                                [], git_dir, warning_ids, entry_ids, 0) == 1, "Should be equal"


def test_FixAndMoveBackward_warning(mocker):
    mocker.patch("Logger.add_commit")
    mocker.patch("Logger.add_fix")
    mocker.patch("Git.getCurrentRepo", return_value="0")
    mocker.patch("Tracker.getCurrentThread", return_value="0")
    mocker.patch.object(Git, "repo_path", [
        {'thread_id': '0', 'path': os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo"}])
    git_dir = git.Git(os.path.dirname(
        os.path.abspath(__file__)) + "/testInput/TestRepo")
    assert Git.git_checkout(
        "8e5c4554f8602b7ef587fd9a894f78ea64ac1f8a") == None, "Should be equal"
    mocker.patch("Maven.detect_changes", return_value=True)
    assert Maven.commitFilter(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", [
        "", "", "", "", "", "", "", "7ad2954ad5eabb8adf853b9c6be00f208bcc115e",
        "8e5c4554f8602b7ef587fd9a894f78ea64ac1f8a"], 8) == True, "Should return True"
    mocker.patch("Maven.commitFilter", return_value=True)
    assert Maven.maven_build(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo",
                             ["", "", "", "", "", "", "", "7ad2954ad5eabb8adf853b9c6be00f208bcc115e",
                              "8e5c4554f8602b7ef587fd9a894f78ea64ac1f8a"], 8)[
        "default_build_file_path"] == os.path.dirname(os.path.abspath(
            __file__)) + "/testInput/TestRepo" + os.path.sep + "target" + os.path.sep + "my_app-0.0.1-SNAPSHOT.jar", "Should be the same"
    assert Spotbugs.run_spotbugs(0, "", [], "", "", "", "", "",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/reports/",
                                 "8e5c4554f8602b7ef587fd9a894f78ea64ac1f8a",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/TestRepo/target/my_app-0.0.1-SNAPSHOT.jar",
                                 0) == None, "Should return None"
    warnings = parse_xml(os.path.dirname(os.path.abspath(
        __file__)) + "/testInput/reports/spotbugs_report__00_8e5c4554f8602b7ef587fd9a894f78ea64ac1f8a_my_app-0.0.1-SNAPSHOT.xml",
        os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", warning_ids)
    assert len(warnings) == 0, "Should be equal"
    mocker.patch("Parser.parse_xml", return_value=warnings)
    mocker.patch.object(Tracker, "threadsData", {'0': {'newCommitParsed': {}, 'originCommitParsed': {
        "commit_id": '7ad2954ad5eabb8adf853b9c6be00f208bcc115e', "warnings": [{'origin_location': {
            'commit_id': 'eaf14894', 'file': 'src/main/java/my_app/Main.java', 'startLineNumber': 5,
            'endLineNumber': 5}, 'new_location': {'file': 'src/main/java/my_app/Main.java', 'startLineNumber': '7',
                                                  'endLineNumber': '7'}, 'warning_name': 'MS_SHOULD_BE_FINAL'}]},
        'projectFixes': [], 'fixes': []}})
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "8e5c4554f8602b7ef587fd9a894f78ea64ac1f8a",
                                [], git_dir, warning_ids, entry_ids, 0) == 1, "Should be equal"


def test_FixAndMoveForward_warning(mocker):
    mocker.patch("Logger.add_commit")
    mocker.patch("Logger.add_fix")
    mocker.patch("Git.getCurrentRepo", return_value="0")
    mocker.patch("Tracker.getCurrentThread", return_value="0")
    mocker.patch.object(Git, "repo_path", [
        {'thread_id': '0', 'path': os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo"}])
    git_dir = git.Git(os.path.dirname(
        os.path.abspath(__file__)) + "/testInput/TestRepo")
    assert Git.git_checkout(
        "cf313a918d036d508e6803e9e56bd7ddb4ac4030") == None, "Should be equal"
    mocker.patch("Maven.detect_changes", return_value=True)
    assert Maven.commitFilter(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", [
        "7ad2954ad5eabb8adf853b9c6be00f208bcc115e", "cf313a918d036d508e6803e9e56bd7ddb4ac4030"],
        1) == True, "Should return True"
    mocker.patch("Maven.commitFilter", return_value=True)
    assert Maven.maven_build(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo",
                             ["7ad2954ad5eabb8adf853b9c6be00f208bcc115e",
                                 "cf313a918d036d508e6803e9e56bd7ddb4ac4030"],
                             1)[
        "default_build_file_path"] == os.path.dirname(os.path.abspath(
            __file__)) + "/testInput/TestRepo" + os.path.sep + "target" + os.path.sep + "my_app-0.0.1-SNAPSHOT.jar", "Should be the same"
    assert Spotbugs.run_spotbugs(0, "", [], "", "", "", "", "",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/reports/",
                                 "cf313a918d036d508e6803e9e56bd7ddb4ac4030",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/TestRepo/target/my_app-0.0.1-SNAPSHOT.jar",
                                 0) == None, "Should return None"
    warnings = parse_xml(os.path.dirname(os.path.abspath(
        __file__)) + "/testInput/reports/spotbugs_report__00_cf313a918d036d508e6803e9e56bd7ddb4ac4030_my_app-0.0.1-SNAPSHOT.xml",
        os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", warning_ids)
    assert len(warnings) == 0, "Should be equal"
    mocker.patch("Parser.parse_xml", return_value=warnings)
    mocker.patch.object(Tracker, "threadsData", {'0': {'newCommitParsed': {}, 'originCommitParsed': {
        "commit_id": "a0b684c310f99f85466ed4f765c1f50a855145a1", "warnings": [{"origin_location": {
            "commit_id": "a0b684c3", "file": "src/main/java/my_app/Employee.java", "startLineNumber": 6,
            "endLineNumber":
                6}, "new_location": {"file": "src/main/java/my_app/Employee.java", "startLineNumber": "6",
                                     "endLineNumber": "6"}, "warning_name": "MS_SHOULD_BE_FINAL"}]}, 'projectFixes': [],
        'fixes': []}})
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "cf313a918d036d508e6803e9e56bd7ddb4ac4030",
                                [], git_dir, warning_ids, entry_ids, 0) == 1, "Should be equal"
    fixes = Tracker.threadsData["0"]["fixes"]
    assert fixes[-1]["location"] == "7-7", "Should be equal"


def test_fixLocation_one_line_but_adding_a_line_next_to_it(mocker):
    mocker.patch("Logger.add_commit")
    mocker.patch("Logger.add_fix")
    mocker.patch("Git.getCurrentRepo", return_value="0")
    mocker.patch("Tracker.getCurrentThread", return_value="0")
    mocker.patch.object(Git, "repo_path", [
        {'thread_id': '0', 'path': os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo"}])
    git_dir = git.Git(os.path.dirname(
        os.path.abspath(__file__)) + "/testInput/TestRepo")
    assert Git.git_checkout(
        "6d514851862c22879aeb29f8db92f134b33be3d2") == None, "Should be equal"
    mocker.patch("Maven.detect_changes", return_value=True)
    assert Maven.commitFilter(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", [
        "7ad2954ad5eabb8adf853b9c6be00f208bcc115e", "6d514851862c22879aeb29f8db92f134b33be3d2"],
        1) == True, "Should return True"
    mocker.patch("Maven.commitFilter", return_value=True)
    assert Maven.maven_build(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo",
                             ["7ad2954ad5eabb8adf853b9c6be00f208bcc115e",
                                 "6d514851862c22879aeb29f8db92f134b33be3d2"],
                             1)[
        "default_build_file_path"] == os.path.dirname(os.path.abspath(
            __file__)) + "/testInput/TestRepo" + os.path.sep + "target" + os.path.sep + "my_app-0.0.1-SNAPSHOT.jar", "Should be the same"
    assert Spotbugs.run_spotbugs(0, "", [], "", "", "", "", "",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/reports/",
                                 "6d514851862c22879aeb29f8db92f134b33be3d2",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/TestRepo/target/my_app-0.0.1-SNAPSHOT.jar",
                                 0) == None, "Should return None"
    warnings = parse_xml(os.path.dirname(os.path.abspath(
        __file__)) + "/testInput/reports/spotbugs_report__00_6d514851862c22879aeb29f8db92f134b33be3d2_my_app-0.0.1-SNAPSHOT.xml",
        os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", warning_ids)
    assert len(warnings) == 0, "Should be equal"
    mocker.patch("Parser.parse_xml", return_value=warnings)
    mocker.patch.object(Tracker, "threadsData", {'0': {'newCommitParsed': {}, 'originCommitParsed': {
        "commit_id": "c81076390f567f885485c14c42d9f7ce86a4cf40", "warnings": [{"origin_location": {
            "commit_id": "c8107639", "file": "src/main/java/my_app/Employee.java", "startLineNumber": 5,
            "endLineNumber": 5}, "new_location": {"file": "src/main/java/my_app/Employee.java", "startLineNumber": "5",
                                                  "endLineNumber": "5"}, "warning_name": "MS_SHOULD_BE_FINAL"}]},
        'projectFixes': [], 'fixes': []}})
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "6d514851862c22879aeb29f8db92f134b33be3d2",
                                [], git_dir, warning_ids, entry_ids, 0) == 1, "Should be equal"
    fixes = Tracker.threadsData["0"]["fixes"]
    assert fixes[-1]["location"] == "5-5", "Should be equal"


def test_fix_warning_and_rename_file(mocker):
    mocker.patch("Logger.add_commit")
    mocker.patch("Logger.add_fix")
    mocker.patch("Git.getCurrentRepo", return_value="0")
    mocker.patch("Tracker.getCurrentThread", return_value="0")
    mocker.patch.object(Git, "repo_path", [
        {'thread_id': '0', 'path': os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo"}])
    git_dir = git.Git(os.path.dirname(
        os.path.abspath(__file__)) + "/testInput/TestRepo")
    assert Git.git_checkout(
        "f432d12635ce068ac189c4527d7b6a39f08aa6f2") == None, "Should be equal"
    mocker.patch("Maven.detect_changes", return_value=True)
    assert Maven.commitFilter(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", [
        "", "", "", "", "", "", "", "", "", "bd9a574e391c0be29f0f9dbdf44d3e5c003e2e31",
        "f432d12635ce068ac189c4527d7b6a39f08aa6f2"], 10) == True, "Should return True"
    mocker.patch("Maven.commitFilter", return_value=True)
    assert Maven.maven_build(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo",
                             ["", "", "", "", "", "", "", "", "", "bd9a574e391c0be29f0f9dbdf44d3e5c003e2e31",
                              "f432d12635ce068ac189c4527d7b6a39f08aa6f2"], 10)[
        "default_build_file_path"] == os.path.dirname(os.path.abspath(
            __file__)) + "/testInput/TestRepo" + os.path.sep + "target" + os.path.sep + "my_app-0.0.1-SNAPSHOT.jar", "Should be the same"
    assert Spotbugs.run_spotbugs(0, "", [], "", "", "", "", "",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/reports/",
                                 "f432d12635ce068ac189c4527d7b6a39f08aa6f2",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/TestRepo/target/my_app-0.0.1-SNAPSHOT.jar",
                                 0) == None, "Should return None"
    warnings = parse_xml(os.path.dirname(os.path.abspath(
        __file__)) + "/testInput/reports/spotbugs_report__00_f432d12635ce068ac189c4527d7b6a39f08aa6f2_my_app-0.0.1-SNAPSHOT.xml",
        os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", warning_ids)
    assert len(warnings) == 0, "Should be equal"
    mocker.patch("Parser.parse_xml", return_value=warnings)
    mocker.patch.object(Tracker, "threadsData", {'0': {'newCommitParsed': {}, 'originCommitParsed': {
        "commit_id": "bd9a574e391c0be29f0f9dbdf44d3e5c003e2e31", "warnings": [{"origin_location": {
            "commit_id": "bd9a574e", "file": "src/main/java/my_app/Person.java", "startLineNumber": 4,
            "endLineNumber": 4},
            "new_location": {"file": "src/main/java/my_app/Person.java", "startLineNumber": "4", "endLineNumber": "4"},
            "warning_name": "MS_SHOULD_BE_FINAL"}]}, 'projectFixes': [], 'fixes': []}})
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "f432d12635ce068ac189c4527d7b6a39f08aa6f2",
                                [], git_dir, warning_ids, entry_ids, 0) == 1, "Should be equal"


def test_fix_warning_after_renaming_the_file(mocker):
    mocker.patch("Logger.add_commit")
    mocker.patch("Logger.add_fix")
    mocker.patch("Git.getCurrentRepo", return_value="0")
    mocker.patch("Tracker.getCurrentThread", return_value="0")
    mocker.patch.object(Git, "repo_path", [
        {'thread_id': '0', 'path': os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo"}])
    git_dir = git.Git(os.path.dirname(
        os.path.abspath(__file__)) + "/testInput/TestRepo")
    assert Git.git_checkout(
        "fd7454166006014f1648af9d5e6496b0225c7b81") == None, "Should be equal"
    mocker.patch("Maven.detect_changes", return_value=True)
    assert Maven.commitFilter(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", [
        "", "", "", "", "", "", "", "", "", "", "", "", "05ef822386b0818e868f1308522534cc377b3811",
        "fd7454166006014f1648af9d5e6496b0225c7b81"], 13) == True, "Should return True"
    mocker.patch("Maven.commitFilter", return_value=True)
    assert Maven.maven_build(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo",
                             ["", "", "", "", "", "", "", "", "", "", "", "",
                              "05ef822386b0818e868f1308522534cc377b3811", "fd7454166006014f1648af9d5e6496b0225c7b81"],
                             13)[
        "default_build_file_path"] == os.path.dirname(os.path.abspath(
            __file__)) + "/testInput/TestRepo" + os.path.sep + "target" + os.path.sep + "my_app-0.0.1-SNAPSHOT.jar", "Should be the same"
    assert Spotbugs.run_spotbugs(0, "", [], "", "", "", "", "",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/reports/",
                                 "fd7454166006014f1648af9d5e6496b0225c7b81",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/TestRepo/target/my_app-0.0.1-SNAPSHOT.jar",
                                 0) == None, "Should return None"
    warnings = parse_xml(os.path.dirname(os.path.abspath(
        __file__)) + "/testInput/reports/spotbugs_report__00_fd7454166006014f1648af9d5e6496b0225c7b81_my_app-0.0.1-SNAPSHOT.xml",
        os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", warning_ids)
    assert len(warnings) == 0, "Should be equal"
    mocker.patch("Parser.parse_xml", return_value=warnings)
    mocker.patch.object(Tracker, "threadsData", {'0': {'newCommitParsed': {}, 'originCommitParsed': {
        "commit_id": "05ef822386b0818e868f1308522534cc377b3811", "warnings": [{"origin_location": {
            "commit_id": "368b17da", "file": "src/main/java/my_app/Worker.java", "startLineNumber": 4,
            "endLineNumber": 4}, "new_location": {"file": "src/main/java/my_app/Employee.java", "startLineNumber": "4",
                                                  "endLineNumber": "4"}, "warning_name": "MS_SHOULD_BE_FINAL"}]},
        'projectFixes': [], 'fixes': []}})
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "fd7454166006014f1648af9d5e6496b0225c7b81",
                                [], git_dir, warning_ids, entry_ids, 0) == 1, "Should be equal"


def test_fix_two_warnings_next_to_each_other(mocker):
    mocker.patch("Logger.add_commit")
    mocker.patch("Logger.add_fix")
    mocker.patch("Git.getCurrentRepo", return_value="0")
    mocker.patch("Tracker.getCurrentThread", return_value="0")
    mocker.patch.object(Git, "repo_path", [
        {'thread_id': '0', 'path': os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo"}])
    git_dir = git.Git(os.path.dirname(
        os.path.abspath(__file__)) + "/testInput/TestRepo")
    assert Git.git_checkout(
        "3d651da857347555c2cfb26e5f855b3ec830980e") == None, "Should be equal"
    mocker.patch("Maven.detect_changes", return_value=True)
    assert Maven.commitFilter(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", [
        "05ef822386b0818e868f1308522534cc377b3811", "3d651da857347555c2cfb26e5f855b3ec830980e"],
        1) == True, "Should return True"
    mocker.patch("Maven.commitFilter", return_value=True)
    assert Maven.maven_build(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo",
                             ["05ef822386b0818e868f1308522534cc377b3811",
                                 "3d651da857347555c2cfb26e5f855b3ec830980e"],
                             1)[
        "default_build_file_path"] == os.path.dirname(os.path.abspath(
            __file__)) + "/testInput/TestRepo" + os.path.sep + "target" + os.path.sep + "my_app-0.0.1-SNAPSHOT.jar", "Should be the same"
    assert Spotbugs.run_spotbugs(0, "", [], "", "", "", "", "",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/reports/",
                                 "3d651da857347555c2cfb26e5f855b3ec830980e",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/TestRepo/target/my_app-0.0.1-SNAPSHOT.jar",
                                 0) == None, "Should return None"
    warnings = parse_xml(os.path.dirname(os.path.abspath(
        __file__)) + "/testInput/reports/spotbugs_report__00_3d651da857347555c2cfb26e5f855b3ec830980e_my_app-0.0.1-SNAPSHOT.xml",
        os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", warning_ids)
    assert len(warnings) == 0, "Should be equal"
    mocker.patch("Parser.parse_xml", return_value=warnings)
    mocker.patch.object(Tracker, "threadsData", {'0': {'newCommitParsed': {}, 'originCommitParsed': {
        "commit_id": "c369751e0fc903b167bc8145ac5ba942d7fce9e1", "warnings": [{"origin_location": {
            "commit_id": "c369751e", "file": "src/main/java/my_app/Employee.java", "startLineNumber": 5,
            "endLineNumber": 5}, "new_location": {"file": "src/main/java/my_app/Employee.java", "startLineNumber": "5",
                                                  "endLineNumber": "5"}, "warning_name":
            "MS_SHOULD_BE_FINAL"}, {
            "origin_location": {
                "commit_id": "c369751e",
                "file": "src/main/java/my_app/Employee.java",
                "startLineNumber": 4,
                "endLineNumber": 4},
            "new_location": {
                "file": "src/main/java/my_app/Employee.java",
                "startLineNumber": "4",
                "endLineNumber": "4"},
            "warning_name": "MS_SHOULD_BE_FINAL"}]},
        'projectFixes': [], 'fixes': []}})
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "3d651da857347555c2cfb26e5f855b3ec830980e",
                                [], git_dir, warning_ids, entry_ids, 0) == 2, "Should be equal"


def test_fix_two_warnings_separated_by_lines(mocker):
    mocker.patch("Logger.add_commit")
    mocker.patch("Logger.add_fix")
    mocker.patch("Git.getCurrentRepo", return_value="0")
    mocker.patch("Tracker.getCurrentThread", return_value="0")
    mocker.patch.object(Git, "repo_path", [
        {'thread_id': '0', 'path': os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo"}])
    git_dir = git.Git(os.path.dirname(
        os.path.abspath(__file__)) + "/testInput/TestRepo")
    assert Git.git_checkout(
        "059d36f596eb6177371aae45c1dd6089aa4b3463") == None, "Should be equal"
    mocker.patch("Maven.detect_changes", return_value=True)
    assert Maven.commitFilter(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", [
        "05ef822386b0818e868f1308522534cc377b3811", "059d36f596eb6177371aae45c1dd6089aa4b3463"],
        1) == True, "Should return True"
    mocker.patch("Maven.commitFilter", return_value=True)
    assert Maven.maven_build(os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo",
                             ["05ef822386b0818e868f1308522534cc377b3811",
                                 "059d36f596eb6177371aae45c1dd6089aa4b3463"],
                             1)[
        "default_build_file_path"] == os.path.dirname(os.path.abspath(
            __file__)) + "/testInput/TestRepo" + os.path.sep + "target" + os.path.sep + "my_app-0.0.1-SNAPSHOT.jar", "Should be the same"
    assert Spotbugs.run_spotbugs(0, "", [], "", "", "", "", "",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/reports/",
                                 "059d36f596eb6177371aae45c1dd6089aa4b3463",
                                 os.path.dirname(os.path.abspath(
                                     __file__)) + "/testInput/TestRepo/target/my_app-0.0.1-SNAPSHOT.jar",
                                 0) == None, "Should return None"
    warnings = parse_xml(os.path.dirname(os.path.abspath(
        __file__)) + "/testInput/reports/spotbugs_report__00_059d36f596eb6177371aae45c1dd6089aa4b3463_my_app-0.0.1-SNAPSHOT.xml",
        os.path.dirname(os.path.abspath(__file__)) + "/testInput/TestRepo", warning_ids)
    assert len(warnings) == 0, "Should be equal"
    mocker.patch("Parser.parse_xml", return_value=warnings)
    mocker.patch.object(Tracker, "threadsData", {'0': {'newCommitParsed': {}, 'originCommitParsed': {
        "commit_id": "a86812d2c179ae73e10c38ed44344d50fccde8da", "warnings": [{"origin_location": {
            "commit_id": "a86812d2", "file": "src/main/java/my_app/Employee.java", "startLineNumber": 6,
            "endLineNumber": 6}, "new_location": {"file": "src/main/java/my_app/Employee.java", "startLineNumber": "6",
                                                  "endLineNumber": "6"}, "warning_name":
            "MS_SHOULD_BE_FINAL"}, {
            "origin_location": {
                "commit_id": "a86812d2",
                "file": "src/main/java/my_app/Employee.java",
                "startLineNumber": 4,
                "endLineNumber": 4},
            "new_location": {
                "file": "src/main/java/my_app/Employee.java",
                "startLineNumber": "4",
                "endLineNumber": "4"},
            "warning_name": "MS_SHOULD_BE_FINAL"}]},
        'projectFixes': [], 'fixes': []}})
    assert parseAndCheckReports(os.path.dirname(os.path.abspath(__file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/reports",
                                os.path.dirname(os.path.abspath(
                                    __file__)) + "/testInput/TestRepo",
                                "https://github.com/RustyPincer/TestRepo", "059d36f596eb6177371aae45c1dd6089aa4b3463",
                                [], git_dir, warning_ids, entry_ids, 0) == 2, "Should be equal"


def test_finding_file():
    assert find_file("the/path/a.txt", os.path.dirname(os.path.abspath(__file__)
                                                       ) + "/testInput") == True, "Should be found"
    assert find_file("the/path/b.txt", os.path.dirname(os.path.abspath(__file__)
                                                       ) + "/testInput") == False, "Should be not found"
    assert find_file("y/a.txt", os.path.dirname(os.path.abspath(__file__)
                                                ) + "/testInput") == False, "Should be not found"


def test_parse_xml(mocker):
    mocker.patch("Parser.find_file", return_value=True)
    with open(os.path.dirname(os.path.abspath(__file__)) + "/testInput/parse_xml/parsed_xml.txt") as file:
        parsed_xml = file.read()
        assert str(parse_xml(os.path.dirname(os.path.abspath(__file__)) +
                             "/testInput/parse_xml/xml_to_parse.xml", "",
                             warning_ids)) == parsed_xml, "Should be the same"
    with open(os.path.dirname(os.path.abspath(__file__)) + "/testInput/parse_xml/parsed_xml_wrong.txt") as file:
        parsed_xml = file.read()
        assert str(parse_xml(os.path.dirname(os.path.abspath(__file__)) +
                             "/testInput/parse_xml/xml_to_parse.xml", "",
                             warning_ids)) != parsed_xml, "Should not be the same"
    with open(os.path.dirname(
            os.path.abspath(__file__)) + "/testInput/parse_xml/parsed_xml_multiple_sourceLine.txt") as file:
        parsed_xml = file.read()
        assert str(parse_xml(os.path.dirname(os.path.abspath(__file__)) +
                             "/testInput/parse_xml/xml_to_parse_multiple_sourceLine.xml", "",
                             warning_ids)) == parsed_xml, "Should be the same"
    assert parse_xml(os.path.dirname(os.path.abspath(__file__)) +
                     "/testInput/parse_xml/xml_to_parse_empty.xml", "", warning_ids) == [], "Should be the same"
    assert parse_xml(os.path.dirname(os.path.abspath(__file__)) +
                     "/testInput/parse_xml/not_existing.xml", "", warning_ids) == [], "Should be the same"
    assert parse_xml(os.path.dirname(os.path.abspath(__file__)) +
                     "/testInput/parse_xml/not_xml.txt", "", warning_ids) == [], "Should be the same"


class TestDecorator(unittest.TestCase):
    @patch('subprocess.Popen.communicate', side_effect=time.sleep(10))
    def test_Decorator_timeout(self, mocker):
        mocker.patch.object(print_command, "timeout", 1)
        run_command = print_command(subprocess.Popen)
        self.assertRaises(Exception, run_command,
                          [
                              "mvn",
                              "package",
                              "-q",
                              "-Dmaven.test.skip=true",
                              "-Dmaven.javadoc.skip=true",
                              "-Dsource.skip",
                          ]
                          )


def test_check_commit_year(mocker):
    mocker.patch.object(Maven, "valid_commit_year", "2020")
    assert Maven.check_commit_year("8bb2da7683a732a5662ed7285fc6e9caa0f2d5a8", os.path.dirname(
        os.path.abspath(__file__)) + "/testInput/commitYearTest") == True, "Should be True"
    mocker.patch.object(Maven, "valid_commit_year", "2030")
    assert Maven.check_commit_year("8bb2da7683a732a5662ed7285fc6e9caa0f2d5a8", os.path.dirname(
        os.path.abspath(__file__)) + "/testInput/commitYearTest") == False, "Should be False"


def test_search_java_files():
    assert Maven.search_java_files(os.path.dirname(os.path.abspath(
        __file__)) + "/testInput/search_java_files/no_java_file") == True, "Should be true"
    assert Maven.search_java_files(os.path.dirname(os.path.abspath(
        __file__)) + "/testInput/search_java_files/with_java_file") == False, "Should be false"


def test_tracker(mocker):
    mocker.patch("Logger.add_commit")
    mocker.patch("Parser.parse_xml", return_value={"status": 404})
    assert parseAndCheckReports(
        "", "", "", "", "", "", [], [], [], "") == None, "Should be None"


def test_mavenBuild(mocker):
    mocker.patch("Logger.add_commit")
    mocker.patch("Maven.commitFilter", return_value=False)
    assert Maven.maven_build("", "", "") == False, "Should return False"


def test_commitFilter_one_False(mocker):
    mocker.patch("Logger.add_commit")
    mocker.patch("Maven.check_commit_year", return_value=False)
    assert Maven.commitFilter("", "s", 0) == False, "Should return False"


def test_commitFilter_all_True(mocker):
    mocker.patch("Logger.add_commit")
    mocker.patch("Maven.check_commit_year", return_value=True)
    mocker.patch("Maven.search_java_files", return_value=False)
    mocker.patch("Maven.detect_changes", return_value=True)
    mocker.patch("os.path.exists", return_value=True)
    assert Maven.commitFilter("", "ss", 1) == True, "Should return True"


def test_commitFilter_all_False(mocker):
    mocker.patch("Logger.add_commit")
    mocker.patch("Maven.check_commit_year", return_value=False)
    mocker.patch("Maven.search_java_files", return_value=True)
    mocker.patch("Maven.detect_changes", return_value=False)
    mocker.patch("os.path.exists", return_value=False)
    assert Maven.commitFilter("", "ss", 1) == False, "Should return False"


def test_deleting():
    os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/testInput")
    delete_folder(os.path.dirname(os.path.abspath(__file__)) +
                  "/testInput/reports/", "", "")
    delete_folder(os.path.dirname(os.path.abspath(__file__)) +
                  "/testInput/OneCommitRepo/", "", "")
    delete_folder(os.path.dirname(os.path.abspath(__file__)) +
                  "/testInput/commitYearTest", "", False)
    assert isdir(os.path.dirname(os.path.abspath(__file__)) +
                 "/testInput/commitYearTest") == False, "Should be False"
    delete_folder(os.path.dirname(os.path.abspath(__file__)) +
                  "/testInput/TestRepo", "", False)
    assert isdir(os.path.dirname(os.path.abspath(__file__)) +
                 "/testInput/TestRepo") == False, "Should be False"


def test_spotbugs(mocker):
    mocker.patch("Logger.add_project")
    assert Spotbugs.run_spotbugs(
        "", "", "", "", "", "", "", "", "", "", "", 0) == False, "Should return False"


if __name__ == "__main__":
    test_deleting()
    test_cloning(mocker)
    test_finding_file()
    test_parse_xml(mocker)
    test_check_commit_year(mocker)
    test_search_java_files()
