# Model:
# - code with <extra_id_0>
# - target_code

import re
import pandas as pd
from random import choice, randint


def clean(string):
    string = string.strip()
    string = string.replace('\n', ' ')
    string = string.replace('\\n', ' ')
    string = string.replace('\t', ' ')
    string = string.replace('\\t', ' ')
    string = re.sub('\\s+', ' ', string)
    return string


x = []


def mask(string):
    lines = string.split('<NEW_LINE>')
    idx = -1
    line = ''
    attempts = 10
    while len(line) == 0 or line == '{' or line == '}':
        if attempts == 0:
            break
        idx = randint(1, len(lines) - 2)
        line = clean(lines[idx])
        attempts -= 1

    if attempts == 0:
        while len(line) == 0:
            idx = randint(1, len(lines) - 2)
            line = clean(lines[idx])

    random_integer = randint(1, 10)
    initial = random_integer

    inverted = line[::-1]
    separators = [' ', ';', ':', '=', '{', '}', '(', ')', '[', ']', '.', ',', '"', "'", '^', '|', '&', '+', '-', '*', '/', '%', '<', '>', '!', '?', '@', '#', '$', '~']
    i = 0
    for i in range(len(inverted)):
        if random_integer == 0:
            break
        if inverted[i] in separators:
            random_integer -= 1
    if i == len(inverted) - 1:
        i += 1
    masked_code = inverted[:i]
    masked_code = masked_code[::-1]

    if masked_code.startswith(' '):
        x.append(initial - random_integer - 1)
        masked_code = masked_code[1:]
    else:
        x.append(initial - random_integer)

    line = line.replace(masked_code, '<extra_id_0>')

    if 'extra_id_0' not in line:
        raise Exception('extra_id_0 not in line')

    lines[idx] = line
    lines = clean(' '.join(lines))

    return lines, masked_code


def main2():
    df = pd.read_csv('../awork/work.csv')

    for idx, row in df.iterrows():
        masked_method, masked_code = mask(row['code'])
        df.at[idx, 'masked_method'] = masked_method
        df.at[idx, 'masked_code'] = masked_code

    # with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.max_colwidth', -1):
    #     print(df.head())

    df.to_csv('../awork/work_masked.csv', index=False)
    with open('../awork/token_test.tsv', 'w') as f:
        for idx, row in df.iterrows():
            f.write(f'{row["masked_method"]}\t{row["masked_code"]}\n')

    import numpy as np
    print(np.mean(x))
    print(np.std(x))
    y = [0] * 10
    for xi in x:
        y[xi - 1] += 1
    for i in range(len(y)):
        print(f'{i + 1}\t{y[i]}')

    # 3.994967978042086
    # 2.3315082592448646
    # 1	1760
    # 2	1610
    # 3	1789
    # 4	1483
    # 5	1631
    # 6	857
    # 7	667
    # 8	588
    # 9	364
    # 10	181


def main():
    # Evaluation:
    # - id: the id of the prediction
    # - predicted_method: the predicted method as a whole
    # - masked_code: the code that was masked by the user
    # - predicted_code: the code that was predicted by the model

    df = pd.read_csv('../awork/work_masked.csv')
    df = df.drop(columns=['code'])

    with open('../awork/data/predictions.txt', 'r') as f:
        predictions = f.read().strip().split('\n')

    df['predicted_code'] = predictions
    for idx, row in df.iterrows():
        df.at[idx, 'predicted_method'] = row['masked_method'].replace('<extra_id_0>', row['predicted_code'])

    df = df.drop(columns=['masked_method'])
    # with pd.option_context('display.max_rows', None, 'display.max_columns', None, 'display.max_colwidth', -1):
    #     print(df.head())

    df.to_csv('../awork/to_evaluate.csv', index=False)


if __name__ == '__main__':
    main()
