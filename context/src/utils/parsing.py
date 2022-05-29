import os


def parse_mask(base_path):
    mask_file = os.path.join(base_path, 'mask.txt')
    with open(mask_file, "r") as f:
        lines = [line.strip() for line in f.readlines()]
        return lines


def parse_masked_code(base_path):
    masked_code_file = os.path.join(base_path, 'masked_code.txt')
    with open(masked_code_file, "r") as f:
        lines = [line.strip() for line in f.readlines()]
        return lines


def parse_tracing(base_path):
    tracing_file = os.path.join(base_path, 'tracing.txt')
    with open(tracing_file, "r") as f:
        lines = [line.strip() for line in f.readlines()]
        lines = [line.split(',') for line in lines]
        lines = [line[0] for line in lines]
        lines = [int(line) for line in lines]
        return lines
