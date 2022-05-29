import os
import shutil
from argparse import ArgumentParser


def create_directory_if_needed(path):
    if not os.path.exists(path):
        os.makedirs(path)


files = [
    'android_block_inputs',
    'android_block_targets',
    'android_construct_inputs',
    'android_construct_targets',
    'android_token_inputs',
    'android_token_targets',
    'java_block_inputs',
    'java_block_targets',
    'java_construct_inputs',
    'java_construct_targets',
    'java_token_inputs',
    'java_token_targets'
]


def is_valid_input_file(parser, arg):
    if os.path.isdir(arg):
        listed_files = os.listdir(arg)
        if len(listed_files) == 12:
            for file in files:
                if file not in listed_files:
                    parser.error(f'{file} is missing')
            return arg
    parser.error("The input file must be a directory containing 12 files.")


def CLI():
    parser = ArgumentParser(description='Inputs and targets concatenator')

    parser.add_argument('--input', '-i', dest='input', required=True,
                        help='Input folder with the 12 files',
                        type=lambda x: is_valid_input_file(parser, x))

    parser.add_argument('-o', '--output', dest='output', required=False,
                        help='Output folder',
                        default='./out')

    args = parser.parse_args()
    return args


def main():
    args = CLI()
    create_directory_if_needed(args.output)

    with open(os.path.join(args.output, 'inputs.txt'), 'w') as inputs, \
            open(os.path.join(args.output, 'targets.txt'), 'w') as targets:
        for dataset in ['android', 'java']:
            for level in ['block', 'construct', 'token']:
                input_file = os.path.join(args.input, f'{dataset}_{level}_inputs')
                target_file = os.path.join(args.input, f'{dataset}_{level}_targets')
                with open(input_file) as i, open(target_file) as t:
                    for line in i:
                        inputs.write(line)
                    for line in t:
                        targets.write(line)
                if not (dataset == 'java' and level == 'token'):
                    inputs.write('\n')
                    targets.write('\n')


if __name__ == '__main__':
    main()
