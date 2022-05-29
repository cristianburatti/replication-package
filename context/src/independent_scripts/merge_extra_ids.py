import os
import re
import shutil
import pandas as pd
from progress_bar import ProgressBar


def create_directory_if_needed(path):
    if not os.path.exists(path):
        os.makedirs(path)


def main():
    df = pd.read_csv('data/language_dataset.tsv', sep='\t', header=None, names=['left', 'right'])
    bar = ProgressBar(df)

    create_directory_if_needed('out')

    bad_format_count = 0

    with open("out/extra_ids.txt", 'w') as f:
        for idx, row in df.iterrows():
            bar.update(f'bad format {bad_format_count}')
            bar.next()
            left, right = row['left'], row['right']
            left = re.split(r'<extra_id_\d+>', left)
            right = re.split(r'<extra_id_\d+>', right)

            if len(left) != (len(right) - 1):
                if len(left) == 101 and len(right) == 101:
                    bad_format_count += 1
                else:
                    print()
                    print(f'Error at {idx}')
                    exit()

            method = ''
            for i in range(len(left)):
                method += (right[i] + left[i])
            method += right[-1]

            stripped = ''.join(method.split())

            f.write(stripped + '\n')

    bar.finish()


if __name__ == '__main__':
    main()
