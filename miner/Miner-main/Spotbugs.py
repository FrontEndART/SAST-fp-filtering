"""
    This is module can run Spotbugs on jar, war, ear or zip files.
"""

import subprocess
from Decorator import print_command, try_except
import os
import platform

run_command = print_command(subprocess.Popen)
opsys = platform.system()


@try_except
def run_spotbugs(spotbugs_loc, reports, commit, jar_war_ear_zip, num):
    """
    Running spotbugs
    :param spotbugs_loc: The location where the Spotbugs is found
    :param reports: The folder where the XML files can generated to
    :param commit: The commit we are in
    :param jar_war_ear_zip: The jar, war, ear or zip file we need to run Spotbugs on
    :param num: The ordinal number of the commit
    """
    file_name = os.path.basename(jar_war_ear_zip)
    if spotbugs_loc == "":
        command = ["spotbugs"]
        if opsys == "Windows":
            command = ["spotbugs.jar"]
    else:
        command = ["java", "-jar", spotbugs_loc]
    command += ["-textui",
                "-low",
                "-xml="
                + reports
                + "spotbugs_report__{:02d}_{}_{}.xml".format(
                    num, commit, file_name.rsplit(".", 1)[0]),
                jar_war_ear_zip]
    if opsys == "Windows":
        run_command(
            f"spotbugs {file_name}",
            command,
            shell=True,
            stdout=subprocess.PIPE,
        )
    else:
        run_command(
            f"spotbugs {file_name}",
            command,
            stderr=subprocess.PIPE,
        )
