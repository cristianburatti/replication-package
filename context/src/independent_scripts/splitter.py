import os
from argparse import ArgumentParser


def CLI():
    parser = ArgumentParser(description='Inputs and targets concatenator')

    parser.add_argument('-o', '--operation', type=str, required=True,
                        help='Operation to perform: merge files or split',
                        choices=['merge', 'split'])

    parser.add_argument('-i', '--ids_dir', type=str, required=False, help='Directory with ids files')

    args = parser.parse_args()
    return args


def merge_files():
    datasets = ['android', 'java']
    levels = ['block', 'construct', 'token']
    scopes = ['test', 'train']

    for level in levels:
        with open(f'out/{level}.tsv', 'w') as f_out:
            for dataset in datasets:
                for scope in scopes:
                    with open(f'merge_datasets/{scope}_{dataset}_{level}.tsv') as f_in:
                        for line in f_in:
                            f_out.write(line)


def count_lines(file_path):
    count = 0
    with open(file_path) as f:
        for line in f:
            if line.strip():
                count += 1
    return count


def out_ids(name, ids):
    with open(f'out/{name}.txt', 'w') as f:
        for idx in ids:
            f.write(f'{idx}\n')


def split_files(args):
    levels = ['token', 'block', 'construct']

    if args.ids_dir:
        with open(os.path.join(args.ids_dir, 'eval.txt')) as f_eval, \
                open(os.path.join(args.ids_dir, 'train.txt')) as f_train, \
                open(os.path.join(args.ids_dir, 'test.txt')) as f_test:
            eval_ids = set([line.strip() for line in f_eval])
            train_ids = set([line.strip() for line in f_train])
            test_ids = set([line.strip() for line in f_test])
    else:
        eval_ids = set()
        test_ids = set()
        train_ids = set()

    for level in levels:
        total_size = count_lines(f'merge_datasets/{level}.tsv')
        eval_count = 0
        test_count = 0
        size = int(total_size * 0.1)

        with open(f'merge_datasets/{level}.tsv') as f_in, \
                open(f'out/{level}_eval.tsv', 'w') as f_eval, \
                open(f'out/{level}_test.tsv', 'w') as f_test, \
                open(f'out/{level}_train.tsv', 'w') as f_train:

            for line in f_in:
                row = line.split('\t')
                idx = row[0]
                entry = f'{row[1]}\t{row[2]}'

                if idx in eval_ids:
                    f_eval.write(entry)
                    eval_count += 1
                elif idx in test_ids:
                    f_test.write(entry)
                    test_count += 1
                elif idx in train_ids:
                    f_train.write(entry)

                if not args.ids_dir:
                    if eval_count < size:
                        f_eval.write(entry)
                        eval_count += 1
                        eval_ids.add(idx)
                    elif test_count < size:
                        f_test.write(entry)
                        test_count += 1
                        test_ids.add(idx)
                    else:
                        f_train.write(entry)
                        train_ids.add(idx)

    if not args.ids_dir:
        out_ids('eval', eval_ids)
        out_ids('test', test_ids)
        out_ids('train', train_ids)


def main():
    args = CLI()

    if args.operation == 'merge':
        merge_files()
    elif args.operation == 'split':
        split_files(args)


if __name__ == '__main__':
    main()
