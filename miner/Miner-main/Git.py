"""
    This is module contains all git functions.
"""

import git
import subprocess
from subprocess import check_output, STDOUT
from Decorator import print_command, try_except, printOutput
import threading

run_command = print_command(subprocess.Popen)
stdPrint = printOutput(print)
list = try_except(list)
repo = []
git_dir = []
repo_path = []


@try_except
def git_fetch(repo_dir, repo_link, thread_counter, since_date=None, until_date=None):
    """
    Cloning repo and getting commit list and printing it
    :param repo_dir: The directory where we can clone the repo
    :param repo_link: The link of the github repository
    :param thread_counter: The thread number
    :param since_date: The date from which we want to get commits
    :param until_date: The date until which we want to get commits
    :return: The commits of the repo
    """
    if repo_link != "":
        if git_clone(repo_link, repo_dir, thread_counter) == False:
            return False
    
    global repo_path
    global repo
    global git_dir
    found = False
    for path in repo_path:
        if path["thread_id"] == str(thread_counter):
            path["path"] = repo_dir
            found = True
            break
    if not found:
        repo_path.append({"thread_id": str(thread_counter), "path": repo_dir})
    found = False
    for dir in repo:
        if dir["thread_id"] == str(thread_counter):
            dir["dir"] = git.Repo(repo_dir)
            found = True
            break
    if not found:
        repo.append({"thread_id": str(thread_counter), "dir": git.Repo(repo_dir)})

    for dir in repo:
        if dir["thread_id"] == str(thread_counter):
            commits = list(str(repo_link), "", [], "Git error", "Failed to load commit list", "", thread_counter, dir["dir"].iter_commits(dir["dir"].head.name, since=since_date, until=until_date))
    if commits == False:
        return
    commits.reverse()
    stdPrint("Listing commits:", "")
    stringCommits = f"[{commits[0]}"
    for i in range(1, len(commits)):
        stringCommits += f", {commits[i]}"
    stdPrint(stringCommits + "]", "")
    found = False
    for dir in git_dir:
        if dir["thread_id"] == str(thread_counter):
            dir["dir"] = git.Git(repo_dir)
            found = True
            break
    if not found:
        git_dir.append({"thread_id": str(thread_counter), "dir": git.Git(repo_dir)})
    return commits


def gitRestore(file_path):
    """
    Git restoring a file
    :param file_path: The path of the file
    """
    global git_dir
    for dir in git_dir:
        if dir["thread_id"] == getCurrentRepo():
            dir["dir"].restore(file_path)


def getGitDir():
    """
    Returning the git directory
    :return: The git directory
    """
    global git_dir
    for dir in git_dir:
        if dir["thread_id"] == getCurrentRepo():
            return dir["dir"]


def close_repo():
    """
    Closing repo
    """
    global repo
    for dir in repo:
        if dir["thread_id"] == getCurrentRepo():
            dir["dir"].close()


def git_clone(repo_link, repo_dir, thread):
    """
    Cloning repo
    :param repo_link: The link of the github repository
    :param repo_dir: The path to folder where we wan5 to clone repo
    :param thread: The thread number
    :return: If cloning was successful or not
    """
    link = repo_link.split("/")
    clone = try_except(run_command)
    return clone(0, "0", [], "Git error", "Project not found", "", thread,
            f"git clone {repo_link}",
            [
                "git",
                "clone",
                "https://:@github.com/"
                + link[len(link) - 2]
                + "/"
                + link[len(link) - 1],
                repo_dir
            ],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
        )    


def git_checkout(commit):
    """
    Git checkout
    :param commit: The commit we need to checking out to
    """
    global repo_path
    path = ""
    for p in repo_path:
        if p["thread_id"] == getCurrentRepo():
            path = (p["path"])
            break
    check_output(["git", "--git-dir=" + path + "/.git", "--work-tree=" + path, "reset", "--hard"], stderr=STDOUT)
    checkout = try_except(run_command)
    checkout(0, str(commit), [], "Git error", "Git checkout failed", "", getCurrentRepo(),
            f"git ckeckout {commit}",
            [
                "git",
                "--git-dir=" + path + "/.git",
                "--work-tree=" + path,
                "checkout",
                str(commit)
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

def getCurrentRepo():
    """
    Returning cuurent repo
    :return: The current repo
    """
    return threading.currentThread().name