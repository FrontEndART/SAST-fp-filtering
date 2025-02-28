"""
    This module contains all the Maven functions, the pom fixing, filtering functions and other functions, that
    chek if Maven build is necessarry.
"""

import shutil
import tempfile
import xml.etree.ElementTree as ET
import glob
import os
import subprocess
import zipfile
from Decorator import print_command, printOutput
import Logger
import main

valid_commit_year = "2000"
PREFERRED_JAVA_VERSION = "21"
POM_PATH = "pom.xml"

stdPrint = printOutput(print)
run_command = print_command(subprocess.Popen)


def maven_build(repo_dir, commits, i, lastCommit=""):
    """
    Building with Maven
    :param repo_dir: The repo directory we working with
    :param commits: The commits of the repository
    :param i: The ordinal number of the commit we working with
    :param lastCommit: The last commit which was successfully built
    :return: The name of the generated files
    """
    if commitFilter(repo_dir, commits, i) == False:
        return False
    fileName = edit_pom(repo_dir + os.path.sep + POM_PATH)
    changedModules = []
    if lastCommit != "":
        changedModules = modul_changes(repo_dir, lastCommit, commits[i])
        if changedModules == []:
            maven_clean(repo_dir)
    if changedModules == []:
        command = ["mvn", "package", "-q", "-Dmaven.test.skip=true",
                   "-Dmaven.javadoc.skip=true", "-Dsource.skip"]
        if main.opsys == "Windows":
            run_command(
                f"mvn package {repo_dir}",
                command,
                shell=True,
                cwd=repo_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        else:
            run_command(
                f"mvn package {repo_dir}",
                command,
                cwd=repo_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
    else:
        for modulName in changedModules:
            command = ["mvn", "package", "-q", "-pl", modulName, "-am",
                       "-Dmaven.test.skip=true", "-Dmaven.javadoc.skip=true", "-Dsource.skip"]
            if main.opsys == "Windows":
                run_command(
                    f"mvn package {repo_dir}",
                    command,
                    shell=True,
                    cwd=repo_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
            else:
                run_command(
                    f"mvn package {repo_dir}",
                    command,
                    cwd=repo_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )

    return get_generated_files(repo_dir, fileName)


def commitFilter(repo_dir, commits, i):
    """
    Checking if Maven build is necessary or possible or not
    :param repo_dir: The repo directory we working with
    :param commits: The commits of the repository
    :param i: The ordinal number of the commit we working with
    :return: if we need Maven build or not
    """
    if not check_commit_year(commits[i], repo_dir):
        stdPrint("{} is older than {}".format(
            str(commits[i]), valid_commit_year), "")
        stdPrint(f"Skipping commit: {commits[i]}", "")
        Logger.add_commit(str(commits[i]), [],
                          "skipped", "Commit is too old", "")
        return False

    if search_java_files(repo_dir):
        stdPrint(
            f"There is no java file in repo, skipping commit: {commits[i]}", "")
        Logger.add_commit(
            str(commits[i]),
            [],
            "skipped",
            "There is no java file in repo, skipped commit.",
            "",
        )
        return False

    if i > 0:
        if not detect_changes(commits[i], commits[i - 1]):
            stdPrint(f"Skipping commit: {commits[i]}", "")
            Logger.add_commit(
                str(commits[i]),
                [],
                "skipped",
                "No significant change detected, no build needed",
                "",
            )
            return False

    if not os.path.exists(repo_dir + "/pom.xml"):
        stdPrint(f"Missing pom.xml\nSkipping commit: {commits[i]}", "")
        Logger.add_commit(str(commits[i]), [],
                          "skipped", "missing pom.xml", "")
        return False

    return True


def detect_changes(curr, prev):
    """
    Checking if there are changes in java files or not
    :param curr: The current commit
    :param prev: The previous commit
    :return: If there are changes or not
    """
    diff_index = prev.diff(curr)
    for diff in diff_index:
        if diff.a_path.endswith(".java") or diff.b_path.endswith(".java"):
            stdPrint("Change detected in source files", "")
            return True

    stdPrint("No significant change detected, no build needed", "")
    return False


def search_java_files(repo_dir):
    """
    Checking if there are java files in repo or not
    :param repo_dir: The repo directory we working with
    :return: If there are java files or not
    """
    no_java_file = True
    for root, dirs, files in os.walk(repo_dir):
        for file in files:
            if file.endswith(".java"):
                no_java_file = False
                break
    return no_java_file


def check_commit_year(commit, repo_dir):
    """
    Checking if the commit is too old or not
    :param commit: The commit we working with
    :param repo_dir: The repo directory we working with
    :return: The commit is too old or not
    """
    proc = subprocess.Popen(
        [
            "git",
            "--git-dir=" + repo_dir + "/.git",
            "show",
            "-s",
            "--format=%cd",
            "--date=format:%Y",
            str(commit),
        ],
        stdout=subprocess.PIPE,
    )
    out, err = proc.communicate()
    commit_year = out.decode().rstrip()
    if commit_year < valid_commit_year:
        return False
    return True


def get_generated_files(module_path, fileName):
    """
    Search for the generated files we need
    :param module_path: The module path
    :param fileName: Name of file
    """
    targetDirs = []
    jar_war_ear_zips_in_all_target = []
    for root, dirs, files in os.walk(module_path):
        for dir in dirs:
            if dir.split("/")[-1] == "target":
                jar_war_ear_zips = (
                    glob.glob(root + "/target/*.jar")
                    + glob.glob(root + "/target/*.war")
                    + glob.glob(root + "/target/*.ear")
                    + glob.glob(root + "/target/*.zip")
                )
                if len(jar_war_ear_zips) != 0:
                    targetDirs.append(root + "/target")
                    for jwez in jar_war_ear_zips:
                        jar_war_ear_zips_in_all_target.append(jwez)

    if len(targetDirs) == 0:
        raise Exception("Missing target folder!")

    if len(targetDirs) == 1 and targetDirs[0] == module_path + "/target":
        jar_war_ear_zips = (
            glob.glob(module_path + os.path.sep + "target/*.jar")
            + glob.glob(module_path + "/target/*.war")
            + glob.glob(module_path + "/target/*.ear")
            + glob.glob(module_path + "/target/*.zip")
        )
        stdPrint(f"Generated files in {module_path}: \n{jar_war_ear_zips}", "")

        artifact_id = fileName["artifactId"]
        version = fileName["version"]
        fileList = []
        jar_war_ear_zip_name_without_version = artifact_id
        jar_war_ear_zip_name_with_version = artifact_id + "-" + version
        for filePath in jar_war_ear_zips:
            fileList.append(str(filePath).split(os.path.sep)[-1])
        for jar_war_ear_zip in jar_war_ear_zips:
            build_file_name = str(jar_war_ear_zip).split(
                os.path.sep)[-1].rsplit(".", 1)[0]
            if str(build_file_name) == str(jar_war_ear_zip_name_with_version):
                return {
                    "default_build_file_path": jar_war_ear_zip,
                    "module_build_file_list": fileList,
                }
            if str(build_file_name) == str(jar_war_ear_zip_name_without_version):
                return {
                    "default_build_file_path": jar_war_ear_zip,
                    "module_build_file_list": fileList,
                }
        return {"default_build_file_path": "", "module_build_file_list": fileList}

    else:
        fileList = []
        stdPrint(
            f"Generated files in {module_path}: \n{jar_war_ear_zips_in_all_target}", "")
        if os.path.exists(module_path + "/mergedJar.jar"):
            os.remove(module_path + "/mergedJar.jar")
        merge_jar_files(jar_war_ear_zips_in_all_target,
                        module_path + "/mergedJar.jar")
        for filePath in jar_war_ear_zips_in_all_target:
            fileList.append(str(filePath).split(os.path.sep)[-1])
        return {
            "default_build_file_path": module_path + "/mergedJar.jar",
            "module_build_file_list": fileList,
        }


def modul_changes(repo_dir, originalCommit, newCommit):
    """
    Returns the changed modules between 2 commit
    :param repo_dir: The folder of the repo
    :param originalCommit: The last commit we built
    :param newCommit: The current commit
    :return: The list of the changed modules
    """
    p = subprocess.Popen(
        [
            "git",
            "--git-dir=" + repo_dir + "/.git",
            "--work-tree=" + repo_dir,
            "diff",
            "--name-only",
            str(originalCommit),
            str(newCommit),
            repo_dir,
        ],
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    changedModules = []
    stdout, stderr = p.communicate()
    if p.returncode == 0:
        output = str(stdout).split("\\n")
        for line in output:
            dirs = line.split("/")
            for dir in dirs:
                if dir == "src":
                    module = "/".join(dirs[0:dirs.index(dir)])
                    if module not in changedModules:
                        changedModules.append(module)
                    break
    return changedModules


def edit_pom(pom_path):
    """
    Editing pom if it is necessary
    :param pom_path: The path where pom.xml file is
    """
    namespace = ""
    tree = ET.parse(pom_path)
    root = tree.getroot()
    ns = root.tag.split("}")[0].strip("{")
    if ns != "project":
        ET.register_namespace("", ns)
        namespace = "{" + ns + "}"

    artifact_id = ""
    version = ""
    artifactId = root.find(namespace + "artifactId")
    if artifactId is not None:
        artifact_id = artifactId.text
    module_version = root.find(namespace + "version")
    if module_version is not None:
        version = module_version.text

    noVersion = True

    build = root.find(namespace + "build")
    if build is None:
        pass
    else:
        stdPrint("-----CHECKING BUILD CONFIGURATION-----", "")
        edit_build_configuration(build, namespace, noVersion)

    properties = root.find(namespace + "properties")
    if (properties is None) & noVersion:
        child = ET.Element(namespace + "properties")
        root.append(child)
        properties = root.find(namespace + "properties")

    if properties is not None:
        stdPrint("-----CHECKING PROPERTIES-----", "")
        noVersion = edit_properties(properties, namespace)

    tree.write(open(pom_path, "w"), encoding="unicode")

    stdPrint("Pom edited", "")
    return {"artifactId": artifact_id, "version": version}


def edit_build_configuration(build, namespace, noVersion):
    """
    Editing build configuration if it is necessary
    :param build: The build tag
    :param namespace: The namespace
    :param noVersion: Boolean if there is version or not
    """
    plugins = build.find(namespace + "plugins")
    if plugins is None:
        stdPrint("-----PLUGINS ARE MISSING FROM BUILD----", "")
    else:
        for plugin in plugins:
            executions = plugin.find(namespace + "executions")
            if executions is not None:
                for execution in executions:
                    phase = execution.find(namespace + "phase")
                    if phase is not None and phase.text == "never":
                        plugins.remove(plugin)
            configuration = plugin.find(namespace + "configuration")
            if configuration is not None:
                stdPrint("-----CONFIGURATION FOUND WITHIN BUILD----", "")
                source = configuration.find(namespace + "source")
                if source is None:
                    stdPrint(
                        "-----NO SOURCE ELEMENT FOUND IN CONFIGURATION-----", "")
                else:
                    noVersion = False
                    stdPrint(
                        "-----SOURCE ELEMENT FOUND IN CONFIGURATION-----", "")
                    try:
                        if float(source.text) <= float(PREFERRED_JAVA_VERSION):
                            source.text = PREFERRED_JAVA_VERSION
                    except:
                        source.text = PREFERRED_JAVA_VERSION

                target = configuration.find(namespace + "target")
                if target is None:
                    stdPrint(
                        "-----NO TARGET ELEMENT FOUND IN CONFIGURATION-----", "")
                else:
                    noVersion = False
                    stdPrint(
                        "-----SOURCE ELEMENT FOUND IN CONFIGURATION-----", "")
                    try:
                        if float(target.text) <= float(PREFERRED_JAVA_VERSION):
                            target.text = PREFERRED_JAVA_VERSION
                    except:
                        target.text = PREFERRED_JAVA_VERSION
    return noVersion


def edit_properties(properties, namespace):
    """
    Editing properties if it is necessary
    :param properties: The properties tag
    :param namespace: The namespace
    """
    source_element = properties.find(namespace + "maven.compiler.source")
    if source_element is None:
        source_element = ET.Element("maven.compiler.source")
        source_element.text = PREFERRED_JAVA_VERSION
        properties.insert(0, source_element)
        stdPrint("-----SOURCE ELEMENT IS MISSING FROM POM, ADDING 21----", "")
    else:
        stdPrint("-----SOURCE ELEMENT FOUND IN POM-----", "")

    target_element = properties.find(namespace + "maven.compiler.target")
    if target_element is None:
        target_element = ET.Element("maven.compiler.target")
        target_element.text = PREFERRED_JAVA_VERSION
        properties.insert(0, target_element)
        stdPrint("-----TARGET ELEMENT IS MISSING FROM POM, ADDING 21----", "")
    else:
        stdPrint("-----TARGET ELEMENT FOUND IN POM----", "")

    encoding_element = properties.find(
        namespace + "project.build.sourceEncoding")
    if encoding_element is None:
        encoding_element = ET.Element("project.build.sourceEncoding")
        encoding_element.text = "UTF-8"
        properties.insert(0, encoding_element)
        stdPrint("-----ENCODING ELEMENT IS MISSING FROM POM, ADDING UTF-8----", "")
    else:
        stdPrint("-----ENCODING FOUND IN POM----", "")


def maven_clean(repo_dir):
    """
    Maven cleaning
    :param repo_dir: The repo directory we working with
    """
    repo_path = repo_dir + os.path.sep + POM_PATH
    command = ["mvn", "-f", repo_path, "-q", "clean"]
    if main.opsys == "Windows":
        run_command(
            "mvn clean",
            command,
            shell=True,
            stdout=subprocess.PIPE,
        )
    else:
        run_command(
            "mvn clean",
            command,
            stdout=subprocess.PIPE,
        )


def merge_jar_files(jar_war_ear_zips_in_all_target, merged_path):
    """
    Merge jar files into one jar
    :param jar_war_ear_zips_in_all_target: The jar files we need to merge
    :param merged_path: The path where we want to put the merged jar file
    """
    destination_directory = tempfile.mkdtemp(prefix="jarjarbigs")

    for jwez in jar_war_ear_zips_in_all_target:
        directories = extract_archive(jwez)

        for source_directory in directories:
            copy_class_files(source_directory, destination_directory)
            shutil.rmtree(source_directory)

    shutil.make_archive(merged_path, 'zip', destination_directory)
    os.rename(merged_path + ".zip", merged_path)

    shutil.rmtree(destination_directory)


def copy_class_files(source, destination):
    """
    Copying the class files
    :param source: The directory where we want to cpoy files from
    :param destination: The destination of the copied files
    """
    class_files = [y for x in os.walk(source) for y in glob.glob(
        os.path.join(x[0], '*.class'))]

    for class_file in class_files:
        current_path = os.path.dirname(class_file)[len(source):]
        current_path = current_path.replace('WEB-INF/classes/', '')
        current_file = os.path.basename(class_file)
        destination_path = destination + current_path
        if not destination_path.endswith("/"):
            destination_path += "/"

        if not os.path.exists(destination_path):
            os.makedirs(destination_path)

        shutil.copyfile(class_file, destination_path + current_file)


def extract_archive(archive_file):
    """
    Making extract of the jar file
    :param archive_file: The archive file
    :return: The archive directory
    """
    print("[+] Processing " + archive_file)
    temp_dir = tempfile.mkdtemp(prefix="jarjarbigs")

    archive = zipfile.ZipFile(archive_file, 'r')
    try:
        archive.extractall(temp_dir)
    except FileExistsError as file_exists_error:
        print(
            "[?] Warning! The archive \"{archive_file}\" seems to have a broken file structure. Found douplicate file when trying to write to \"{error_filepath}\". Continuing anyway, result most likely incomplete (please check the contents of the affected archive).".format(
                archive_file=archive_file, error_filepath=str(file_exists_error.filename)))

    directories = [temp_dir]

    dir_archives = [y for x in os.walk(temp_dir)
                    for y in glob.glob(os.path.join(x[0], '*.jar'))]
    dir_archives += ([y for x in os.walk(temp_dir)
                     for y in glob.glob(os.path.join(x[0], '*.war'))])
    dir_archives += ([y for x in os.walk(temp_dir)
                     for y in glob.glob(os.path.join(x[0], '*.ear'))])
    dir_archives += ([y for x in os.walk(temp_dir)
                     for y in glob.glob(os.path.join(x[0], '*.zip'))])

    if len(dir_archives) != 0:

        print("[+] new archive(s) found: " + str(dir_archives))

        for new_archive in dir_archives:
            if os.path.isfile(new_archive):
                tmp_dirs = extract_archive(new_archive)
                directories += tmp_dirs
            else:
                print(
                    "[?] Discovered folder which has a .jar \"extension\": " + str(new_archive))

    return directories
