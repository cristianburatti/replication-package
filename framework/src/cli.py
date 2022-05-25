import re
import os.path
from argparse import ArgumentParser
from argparse import Namespace


# Type functions
def is_valid_input_file(parser: ArgumentParser, arg):
    """
    Ensures that the input file exists and is valid
    :param parser: the parser object
    :param arg: the file path provided by the user
    :return: the file path if it exists and is a CSV file
    """

    if os.path.isfile(arg) and arg.endswith('.csv'):
        return arg
    parser.error(f'The file {arg} does not exist or is not a CSV file')


def is_valid_output_dir(parser: ArgumentParser, arg: str):
    """
    Ensures that the output path is valid
    :param parser: the parser object
    :param arg: the output path provided by the user
    :return: the output path if it is not a file and is not the `resources` directory
    """

    if os.path.isfile(arg):
        parser.error(f'The output directory {arg} is a file')
    if arg and os.path.normpath(arg) == os.path.normpath('./resources'):
        parser.error(f'The output directory cannot be the same as the resources directory')
    return arg


def positive_int(parser: ArgumentParser, field: str, x: str):
    """
    Ensures that the value is a positive integer
    :param parser: the parser object
    :param field: the field name used for a more informative error message
    :param x: the value provided by the user
    :return: the value if it is a positive integer
    """

    x = int(x)
    if x >= 0:
        return x
    parser.error(f'Argument "{field}" must be a positive integer')


def valid_percentage(parser: ArgumentParser, field: str, x: str):
    """
    Ensures that the value is a percentage between 0 and 100
    :param parser: the parser object
    :param field: the field name used for a more informative error message
    :param x: the value provided by the user
    :return: the value if it is a percentage between 0 and 100
    """

    x = float(x)
    if 0 <= x <= 100:
        return x
    parser.error(f'Argument "{field}" must be a percentage between 0 and 100')


def valid_time(parser: ArgumentParser, field: str, str_time: str):
    """
    Ensures that the value is a valid time. Can be provided in days, hours or minutes
    :param parser: the parser object
    :param field: the field name used for a more informative error message
    :param str_time: the value provided by the user
    :return: the value in seconds if it is a valid time
    """

    str_time = str_time.strip().lower()
    parsed = re.findall(r'^\d+[mhd]$', str_time)
    if len(parsed) == 1:
        parsed = parsed[0]
        if parsed[-1] == 'm':
            return int(parsed[:-1]) * 60
        elif parsed[-1] == 'h':
            return int(parsed[:-1]) * 3600
        elif parsed[-1] == 'd':
            return int(parsed[:-1]) * 86400
    parser.error(f'Argument "{field}" must be a positive integer followed by a unit of time (m, h or d)')


# Mode functions
def handle_mode(parser: ArgumentParser, args: Namespace, required: list, not_allowed: list):
    """
    Ensures that the required and not allowed parameters are set correctly
    :param parser: the parser object
    :param args: the arguments parsed by the parser
    :param required: the required parameters for the mode
    :param not_allowed: the parameters that are not allowed
    """

    params_values = {
        'input': None,
        'output': None,
        'min': None,
        'max': None,
        'measure': 'none',
        'coverage_type': 'none',
        'coverage_threshold': None,
        'max_eval_time': None,
        'bleu': 'avg'
    }

    for param in required:
        if getattr(args, param) == params_values[param]:
            parser.error(f'Parameter "{param}" is required in mode {args.action}')
    for param in not_allowed:
        if getattr(args, param) != params_values[param]:
            parser.error(f'Parameter "{param}" is not allowed in mode {args.action}')


def handle_mine(parser: ArgumentParser, args: Namespace):
    # Required parameters: input
    # Optional parameters:
    # Not allowed parameters: output, min, max, measure, bleu, coverage_type, coverage_threshold

    required = ['input']
    not_allowed = ['output', 'min', 'max', 'measure', 'bleu', 'coverage_type', 'coverage_threshold', 'max_eval_time']

    handle_mode(parser, args, required, not_allowed)


def handle_generate(parser: ArgumentParser, args: Namespace):
    # Required parameters: output,
    # Optional parameters: min, max, measure, coverage_type, coverage_threshold
    # Not allowed parameters: input, bleu

    required = ['output']
    not_allowed = ['input', 'bleu']

    handle_mode(parser, args, required, not_allowed)

    c_type, c_threshold = args.coverage_type, args.coverage_threshold
    if args.measure != 'none' and (not args.min and not args.max):
        parser.error(f'Either "min" or "max" (or both) are required when setting "measure" to "{args.measure}"')
    elif args.measure == 'none' and (args.min or args.max):
        parser.error(f'"measure" is required when setting "min" or "max"')
    elif (c_type != 'none' and not c_threshold) or (c_type == 'none' and c_threshold):
        parser.error(f'Coverage type and threshold can only be used together.')
    elif args.min and args.max and args.min > args.max:
        parser.error('"min" must be lower than "max"')


def handle_evaluate(parser: ArgumentParser, args: Namespace):
    # Required parameters: input, output
    # Optional parameters: bleu
    # Not allowed parameters: min, max, measure, coverage_type, coverage_threshold

    required = ['input', 'output']
    not_allowed = ['min', 'max', 'measure', 'coverage_type', 'coverage_threshold', 'max_eval_time']

    handle_mode(parser, args, required, not_allowed)


# Main function
def CLI():
    """
    Parses the command line arguments
    :return: the parsed arguments
    """

    parser = ArgumentParser(description='Framework for evaluating AI models')

    parser.add_argument('--action', '-a', type=str, required=True, choices=['mine', 'generate', 'evaluate'],
                        help='Action to perform')

    mine = parser.add_argument_group('Mining')

    mine.add_argument('--input', '-i', dest='input', required=False, help='Input CSV file',
                      type=lambda x: is_valid_input_file(parser, x))

    mine.add_argument('--output', '-o', dest='output', required=False, help='Output directory',
                      type=lambda x: is_valid_output_dir(parser, x))

    generate = parser.add_argument_group('Generate')

    generate.add_argument('--min', '-n', dest='min', required=False, type=lambda x: positive_int(parser, 'min', x),
                          help='Minimum number of "measure" allowed when generating the dataset')
    generate.add_argument('--max', '-x', dest='max', required=False, type=lambda x: positive_int(parser, 'max', x),
                          help='Maximum number of "measure" allowed when generating the dataset')
    generate.add_argument('--measure', '-m', dest='measure', required=False, type=str,
                          choices=['token', 'line', 'none'],
                          default='none', help='The measure to keep track when generating the dataset')

    generate.add_argument('--coverage-type', '-c', dest='coverage_type', required=False, type=str,
                          choices=['instruction', 'line', 'none'], default='none',
                          help='The type of coverage to use when generating the dataset')
    generate.add_argument('--coverage-threshold', '-t', dest='coverage_threshold', required=False,
                          type=lambda x: valid_percentage(parser, 'coverage_threshold', x),
                          help='The minimum percentage of coverage type allowed')

    generate.add_argument('--max-eval-time', '-e', dest='max_eval_time', required=False,
                          type=lambda x: valid_time(parser, 'max_eval_time', x),
                          help='The maximum time allowed for the later evaluation of the generated dataset. '
                               'Can be provided in days, hours or minutes by adding a suffix (d, h or m) to the number')

    evaluate = parser.add_argument_group('Evaluate')

    evaluate.add_argument('--bleu', '-b', dest='bleu', required=False,
                          choices=['a', 'avg', 'average', '1', '2', '3', '4'], default='avg',
                          type=lambda x: 'avg' if x == 'average' or x == 'a' else x,
                          help='The BLEU score to use when evaluating the model')

    args = parser.parse_args()

    if args.action == 'mine':
        handle_mine(parser, args)
    elif args.action == 'generate':
        handle_generate(parser, args)
    elif args.action == 'evaluate':
        handle_evaluate(parser, args)

    return args
