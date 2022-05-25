import os
from collections import Counter
from xml.etree import ElementTree


class ParsingException(Exception):
    """
    Exception raised when parsing fails.
    """
    pass


def cover_percentage(counters: list, relevant_type: str):
    """
    Calculates the percentage of a given type of coverage
    :param counters: the list of counters found in the report
    :param relevant_type: the type of coverage to consider ('INSTRUCTION', 'LINE)
    :return: a formatted string with the percentage of coverage (e.g. '50.00')
    """

    counter = [c for c in counters if c.get('type') == relevant_type][0]
    covered = int(counter.get('covered'))
    missed = int(counter.get('missed'))
    return f'{covered / (covered + missed) * 100:.2f}'


def parse_jacoco_report(report_file: str):
    """
    Parses a JaCoCo report and extract all the methods inside the project that are covered by at least on test
    :param report_file: the path to the report file
    :return: a list where each covered method is represented by a tuple:
        - package name / path (e.g. 'com/example/myproject')
        - file name (e.g. 'MyClass.java')
        - line number where the method starts (e.g. 10)
        - method name (e.g. 'myMethod')
        - instruction coverage (e.g. '50.00')
        - line coverage (e.g. '70.00')
    """

    try:
        tree = ElementTree.parse(report_file)
    except ElementTree.ParseError:
        return []

    root = tree.getroot()
    packages = root.findall('package')

    covered_methods = []

    for package in packages:
        package_name = str(package.get('name'))
        classes = package.findall('class')
        for class_ in classes:
            class_name = str(class_.get('name'))
            source_file = str(class_.get('sourcefilename'))
            methods = class_.findall('method')

            for method in list(methods):
                method_name = str(method.get('name'))
                if method_name == '<init>':
                    method_name = class_name.split('/')[-1]
                    method_name = method_name.split('$')[-1]
                elif method_name == '<clinit>':
                    continue
                try:
                    method_line = int(method.get('line'))
                except TypeError:
                    continue

                # use the 'METHOD' counter to check if the method is covered
                counters = method.findall('counter')
                method_counter = [c for c in counters if c.get('type') == 'METHOD'][0]
                covered = int(method_counter.get('covered'))

                if covered > 0:
                    # use the 'INSTRUCTION' and 'LINE' counters to calculate the coverage
                    instruction_cover = cover_percentage(counters, 'INSTRUCTION')
                    line_cover = cover_percentage(counters, 'LINE')

                    covered_methods.append(
                        (package_name, source_file, method_line, method_name, instruction_cover, line_cover)
                    )

    return covered_methods


def isolate_method(lines, start, method_name):
    """
    Find the exact lines where the method starts and ends
    :param lines: the lines of the source code
    :param start: the presumed start line of the method (JaCoCo is inconsistent in its reporting)
    :param method_name: the name of the method
    :raise ParsingException: if the method cannot be found
    :return: a tuple:
        - the code of the method where the lines are replaced by the <NEW_LINE> token
        - the start line of the method
        - the end line of the method
    """

    # find the line where the method starts
    while method_name not in lines[start]:
        start -= 1
    lines = lines[start:]

    end = 0
    bracket_count = 0
    method_started = False

    # find the line where the method ends by counting the curly brackets
    while bracket_count != 0 or not method_started:
        lines[end] = lines[end].strip()
        for char in lines[end]:
            if char == '{':
                method_started = True
                bracket_count += 1
            elif char == '}':
                bracket_count -= 1
        end += 1
    lines = lines[:end]

    # replace the lines by the <NEW_LINE> token and ensure the parsing is correct
    output = ' <NEW_LINE> '.join(lines)
    counter = Counter(output)
    if counter['{'] != counter['}']:
        raise ParsingException('Bracket mismatch')
    if output[-1] != '}':
        raise ParsingException('Missing closing bracket')
    if len(output.split('<NEW_LINE>')) >= 50:
        raise ParsingException('Method too long')

    return output, start, start + end


def extract_dataset_methods(log, id_generator, repository, repo_id, jacoco_path):
    """
    Parses the jacoco report and extracts the methods that are covered
    :param log: the logger function
    :param id_generator: the id generator function
    :param repository: the base path of the repository
    :param repo_id: the id of the repository inside the repositories.csv file
    :param jacoco_path: the path to the jacoco report
    """

    report_path = os.path.join(repository, jacoco_path)
    covered_methods = parse_jacoco_report(report_path)

    possible_src_directories = ['src', 'src/main/java', 'src/main/resources', 'app', 'app/src/main/java']

    for method in covered_methods:
        package_name, file_name, line_number, method_name, instruction_cover, line_cover = method

        src_dir = None
        for candidate_src_dir in possible_src_directories:
            file_path = os.path.join(repository, candidate_src_dir, package_name, file_name)
            if os.path.isfile(file_path):
                src_dir = candidate_src_dir
                break

        if src_dir is not None:
            file_path = os.path.join(repository, src_dir, package_name, file_name)
            with open(file_path, 'r') as f:
                lines = f.readlines()

                try:
                    output, start, end = isolate_method(lines, line_number, method_name)
                    output = output.replace('"', '""')

                    method_id = id_generator()

                    file = os.path.join(src_dir, package_name, file_name)
                    log(f'{method_id},"{output}"\n', file='expected')
                    log(f'{method_id},{repo_id},{file},{start},{end},{instruction_cover},{line_cover}\n',
                        file='tracing')
                except (IndexError, ParsingException):
                    continue
