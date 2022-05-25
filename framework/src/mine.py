import os
import traceback
import pandas as pd
from datetime import datetime
from git.exc import GitCommandError
from utils.timer import run_with_timer
from utils.progress_bar import ProgressBar
from mine_utils.git_handler import clone_repository, extract_tag
from mine_utils.jacoco_handler import extract_dataset_methods
from mine_utils.parse_file import parse_mvn, parse_gradle
from utils.file_system import create_working_environment, zip_dir, delete_dir, reformat_repo_name, UnzippableError
from mine_utils.inject_dependency import inject_mvn_dependency, inject_gradle_dependency
from mine_utils.compilation import compile_mvn_project, compile_gradle_project, check_mvn_report, check_gradle_report
from mine_utils.mine_exceptions import MineException, NonBuildableException, TimeoutException, InvalidProjectException


def logger():
    """
    Logger function for the resource files
    """

    def log(msg, file):
        with open(f'resources/{file}.csv', 'a') as f:
            f.write(f'{msg}')

    return log


def id_generator():
    """
    Creates a unique id generator
    :return: the id generator
    """

    def generate_id():
        """
        Generates a unique id every time it is called
        The next id is the previous id plus one
        :return: the next id
        """

        nonlocal i
        i += 1
        return i - 1

    i = 0
    return generate_id


def handle_mvn_project(root):
    """
    Works on a maven project.
    Ensures that the project contains the JUnit dependency, injects the JaCoCo dependency, compiles the project and
    checks the report
    :param root: the root of the project
    :raise: TimeoutException if the project takes too long to compile (90 minutes)
    :raise: NonBuildableException if the project is not buildable
    :return: the time taken for the compilation of the project and the path to the JaCoCo report
    """

    pom_file = os.path.join(root, 'pom.xml')
    dependencies = parse_mvn(pom_file)
    inject_mvn_dependency(pom_file, dependencies)
    status, output, elapsed = run_with_timer(target=compile_mvn_project, args=root, timeout=60 * 90)  # 90 minutes

    if not status:
        raise TimeoutException()
    elif not output:
        raise NonBuildableException()

    report_path = check_mvn_report(root)
    return elapsed, report_path


def handle_gradle_project(root):
    """
    Works on a gradle project.
    Ensures that the project contains the JUnit dependency, injects the JaCoCo dependency, compiles the project and
    checks the report
    :param root: the root of the project
    :raise: TimeoutException if the project takes too long to compile (90 minutes)
    :raise: NonBuildableException if the project is not buildable
    :return: the time taken for the compilation of the project and the path to the JaCoCo report
    """

    gradle_file = os.path.join(root, 'build.gradle')
    parse_gradle(gradle_file)
    inject_gradle_dependency(gradle_file)
    status, output, elapsed = run_with_timer(target=compile_gradle_project, args=root, timeout=60 * 90)  # 90 minutes

    if not status:
        raise TimeoutException()
    elif not output:
        raise NonBuildableException()

    report_path = check_gradle_report(root)
    return elapsed, report_path


def analyze(log, method_id_generator, name, repo_id):
    """
    Analyzes the project and writes the results to the log file
    :param log: the log function
    :param method_id_generator: the method id generator used when parsing the JaCoCo report
    :param name: the name of the project
    :param repo_id: the id of the repository
    """

    formatted_name = reformat_repo_name(name)  # name is now repo__{owner}_{name} (e.g. repo__google_guava)
    tmp_save_folder = os.path.join(f'tmp_mine', formatted_name)
    time, report, project_root = float('NaN'), None, None

    try:
        # clone and checkout
        repo = clone_repository(name, tmp_save_folder)
        tag = extract_tag(repo, log)
        log(f'{tag},', file='repositories')

        # look for mvn or gradle file and handle the project accordingly
        for root, _, files in os.walk(tmp_save_folder):
            if 'pom.xml' in files:
                log('mvn,', file='repositories')

                project_root = root
                time, report = handle_mvn_project(root)
                break

            elif 'build.gradle' in files:
                log('gradle,', file='repositories')

                project_root = root
                time, report = handle_gradle_project(root)
                break

        if not project_root:
            log('N/A,', file='repositories')
            raise InvalidProjectException()  # the project is neither a mvn nor a gradle project

        zip_dir(formatted_name)

        # parse JaCoCo report
        extract_dataset_methods(log, method_id_generator, project_root, repo_id, report)

        pre_path = '/'.join(project_root.split('/')[2:])
        log(f'{pre_path},success,{time}', file='repositories')

    except MineException as e:
        # print(f'{e.cause} {time}')
        log(f'N/A,{e.cause},{time}', file='repositories')

    except UnzippableError:
        log(f'N/A,unzippable,{time}', file='repositories')

    except GitCommandError:
        log(f'N/A,N/A,N/A,', file='repositories')  # log N/A for tag, project and root
        log(f'clone_timeout,{time}', file='repositories')

    except Exception as e:
        print(f'\nUnexpected error:\n{e}\n')
        print(traceback.format_exc())

    finally:
        delete_dir(tmp_save_folder)
        log('\n', file='repositories')


def mine(input_file):
    """
    Mines the repositories in the input file
    :param input_file: the CSV file downloaded from the SEART tool. The important column is only `name`
    """

    create_working_environment()

    df = pd.read_csv(input_file, usecols=['name'])

    # utilities
    log = logger()
    generate_method_id = id_generator()
    bar = ProgressBar(df)

    log('id,name,tag,project,root,status,time\n', file='repositories')
    log('method_id,repo_id,file,start,end,instruction_coverage,line_coverage\n', file='tracing')
    log('id,code\n', file='expected')

    # mine the repositories
    for index, row in df.iterrows():
        name = row['name']

        log(f'{index},{name},', file='repositories')
        bar.update(name, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        bar.next()

        analyze(log, generate_method_id, name, index)

    bar.finish()
    delete_dir(f'tmp_mine')
