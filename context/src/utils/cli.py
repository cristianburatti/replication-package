from argparse import ArgumentParser
from context.classes import Extractors
from context.dataset import Dataset

datasets = ['android', 'java']
levels = ['block', 'construct', 'token']
scopes = ['test', 'training']


def is_valid_folder():
    def __is_valid_folder(path):
        return path in folders

    folders = [dataset + '_' + level + '_' + scope for dataset in datasets for level in levels for scope in scopes]
    return __is_valid_folder


def level_set(level):
    return [dataset + '_' + level + '_' + scope for dataset in datasets for scope in scopes]


def CLI():
    parser = ArgumentParser(description='Context Extractor')

    parser.add_argument('--extractor', '-e', dest='extractor',
                        help='Extractor class to use for additional context',
                        type=Extractors, choices=Extractors.__members__.values(),
                        default=Extractors.none)

    parser.add_argument('--dataset', '-s', dest='dataset',
                        help='Dataset to create',
                        type=Dataset, choices=Dataset.__members__.values(),
                        default=Dataset.complete)

    parser.add_argument('--data', '-d', dest='data',
                        help='Path to data file',
                        type=str, default='./data')

    parser.add_argument('--tmp', '-t', dest='tmp',
                        help='Path to temporary directory',
                        type=str, default='./tmp')

    parser.add_argument('--folder', '-f', dest='folders',
                        nargs='+', help='Path to folder(s) to extract context from',
                        type=str, required=True)

    args = parser.parse_args()

    if args.dataset == Dataset.javadoc:
        for folder in args.folders:
            if folder not in levels:
                parser.error(f'Invalid folder: \'{folder}\'.\n'
                             f'Only one of {levels} is allowed when creating the Javadoc dataset.')
        args.folders = [item for folder in args.folders for item in level_set(folder)]
    else:
        folder_checker = is_valid_folder()
        for folder in args.folders:
            if not folder_checker(folder):
                parser.error(f'Invalid folder: \'{folder}\'.')

    return args
