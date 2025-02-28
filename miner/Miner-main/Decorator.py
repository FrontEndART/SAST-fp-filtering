"""
    These features can print all the Maven, Git or other commands, and this module calls all try-catch blocks and catches
    the exceptions.
"""

import functools
import Logger
import datetime
from threading import Timer
import psutil

output = "standard"
timeout = 30

def try_except(func):
    """
    Calling a function with try-catch block
    :param func: The function
    """
    @functools.wraps(func)
    def wrapper_try_except(project, commit_id, build_files, status, error, tracker, thread, *args, **kwargs):
        try:
            value = func(*args, **kwargs)
            return value
        except Exception as e:
            if status == "Project error":
                Logger.add_project_error(project, error)
            elif status == "last delete":
                print("Can't delete repo_dir")
            else:
                print(e)
                if(project != 0):
                    Logger.add_project(project, thread)
                elif error == "":
                    Logger.add_commit(commit_id, build_files, status, e, tracker)
                else:
                    Logger.add_commit(commit_id, build_files, status, error + ": " + str(e), tracker)
                    print(error)
            return False
    return wrapper_try_except

def print_command(func):
    """
    Printing the commands used by a function
    :param func: The function
    """
    @functools.wraps(func)
    def wrapper_print_command(standardPrint=0, *args, **kwargs):
        command = ""
        for word in args[0]:
            command += word + " "
        global output
        if output == "nothing":
            pass
        elif output == "performance":
            start_time = datetime.datetime.now()
        elif output == "standard" and standardPrint != 0:
            if standardPrint != "":
                print(f"\n{standardPrint}")
        else:
            print(f"\n{command}")
        proc = func(*args, **kwargs)
        terminate = lambda process: kill(process.pid)
        timer = Timer(timeout, terminate, [proc])
        try:
            timer.start()
            stdout, stderr = proc.communicate()
        finally:
            timer.cancel()
        
        if proc.returncode == 0:
            if output == "performance":
                end_time = datetime.datetime.now()
                execution_time = end_time - start_time
                formatted_execution_time = str(execution_time.seconds) + "." + str(execution_time.microseconds)[:3]
                print(f"{formatted_execution_time} seconds ==> {standardPrint}")
            elif output != "nothing":
                print("Process has returned with success!")
        else:    
            if output != "nothing" or output != "performance":
                print("Process has failed!")
            if stdout is None:
                exception = stderr.decode()
            elif stderr is None:
                exception = stdout.decode()
            else:
                exception = stdout.decode() if len(stdout.decode()) > len(stderr.decode()) else stderr.decode()
            raise Exception(exception)
    return wrapper_print_command


def kill(proc_pid):
    """
    Killing the process
    :param proc_pid: The process pid
    """
    process = psutil.Process(proc_pid)
    for proc in process.children(recursive=True):
        proc.kill()
    process.kill()

def printOutput(func):
    """
    Printing in given format to std output
    :param func: The function
    """
    @functools.wraps(func)
    def wrapper_printOutput(detailed, standard=0, nothing=0):
        global output
        if output == "nothing" or output == "performance":
            if nothing != 0:
                func(nothing)
        elif output == "standard" and standard != 0:
            if standard != "":
                func(standard)
        else:
            if detailed != "":
                func(detailed)
    return wrapper_printOutput