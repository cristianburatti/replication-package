import sys
import re
import pandas as pd
from progress_bar import ProgressBar


def flatten(string):
    string = string.strip()
    string = string.replace('\n', ' ')
    string = string.replace('\\n', ' ')
    string = string.replace('\t', ' ')
    string = string.replace('\\t', ' ')
    string = re.sub('\\s+', ' ', string)
    return string


def main():
    with open('data/extra_ids.txt', 'r') as f:
        language_entries = set(f.read().splitlines())

    df = pd.read_csv('data/main.csv', usecols=['ID', 'CODE', 'VALID'])
    df = df.set_index('ID')

    bar = ProgressBar(df)

    skip_count = 0

    with open('out/shared_entries.txt', 'w') as f:
        for idx, row in df.iterrows():
            bar.update(f'skipping {skip_count}')
            bar.next()
            if row['VALID']:
                code = flatten(row['CODE'])
                stripped = ''.join(code.split())

                if stripped in language_entries:
                    f.write(f'{idx}\n')
                    skip_count += 1

    bar.finish()


if __name__ == '__main__':
    main()
