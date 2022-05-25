import os
from multiprocessing import Value
from mine_utils.mine_exceptions import NonBuildableException, NoReportException


def compile_project(root: str, command: str, expected_output: str, return_value: Value):
    """
    Compiles a project using the given command.
    :param root: the root directory of the project
    :param command: the command to use to compile the project
    :param expected_output: the expected output of the compilation
    :param return_value: a multiprocess shared value to store the return value of the compilation
    """

    try:
        output = os.popen(f'cd {root}; {command} 2>&1').read()
        return_value.value = expected_output in output
    except (ValueError, UnicodeError):
        return_value.value = False


def compile_mvn_project(root: str, return_value: Value):
    """
    Compiles a maven project
    :param root: the root directory of the project
    :param return_value: a multiprocess shared value to store the return value of the compilation
    """

    compile_project(root, 'mvn clean install -DskipTests', 'BUILD SUCCESS', return_value)
    output = os.popen(f'cd {root}; mvn test 2>&1').read()
    return_value.value = 'BUILD SUCCESS' in output


def compile_gradle_project(root: str, return_value: Value):
    """
    Compiles a gradle project
    :param root: the root directory of the project
    :param return_value: a multiprocess shared value to store the return value of the compilation
    """

    compile_project(root, 'gradle clean build', 'BUILD SUCCESSFUL', return_value)


def check_mvn_report(root: str):
    """
    Checks if the maven project has a JaCoCo report
    To be called after the compilation of the project
    :param root: the root directory of the project
    :raise NoReportException: if the project has no JaCoCo report
    :return: the path to the JaCoCo report
    """

    target_path = os.path.join(root, 'target')
    site_path = os.path.join(target_path, 'site')
    if not os.path.exists(site_path) or 'jacoco' not in os.listdir(site_path):
        raise NoReportException()

    return os.path.join('target', 'site', 'jacoco', 'jacoco.xml')


def check_gradle_report(root: str):
    """
    Checks if the gradle project has a JaCoCo report
    To be called after the compilation of the project
    :param root: the root directory of the project
    :raise NoReportException: if the project has no JaCoCo report
    :return: the path to the JaCoCo report
    """

    build_path = os.path.join(root, 'build')
    reports_path = os.path.join(build_path, 'reports')
    if not os.path.exists(reports_path) or 'jacoco' not in os.listdir(reports_path):
        raise NoReportException()

    return os.path.join('build', 'reports', 'jacoco', 'test', 'jacocoTestReport.xml')
