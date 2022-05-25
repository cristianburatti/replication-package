import csv
import pandas as pd
from utils.file_system import create_directory_if_needed


def generate(output_folder, measure, min_value, max_value, coverage, threshold, eval_time):
    """
    Filters the dataset created during the `mine` phase and generates a new dataset with the specified parameters.
    The new dataset is saved in the `output_folder` directory and is called `dataset.csv`.
    :param output_folder: the directory where the new dataset will be saved
    :param measure: the measure to be used to filter the dataset (line or token [default None])
    :param min_value: the minimum value of the measure
    :param max_value: the maximum value of the measure
    :param coverage: the coverage type to be used to filter the dataset (line or instruction [default None])
    :param threshold: the minimum percentage of the coverage type
    :param eval_time: the maximum evaluation time of the dataset (as an estimation)
    """
    expected, tracing, repositories = [f'resources/{x}.csv' for x in ['expected', 'tracing', 'repositories']]

    expected = pd.read_csv(expected, usecols=['id', 'code'])
    tracing = pd.read_csv(tracing, usecols=['repo_id', 'method_id', 'instruction_coverage', 'line_coverage'])
    repositories = pd.read_csv(repositories, usecols=['id', 'status', 'time'])
    repositories = repositories[repositories['status'] == 'success'].drop(columns=['status'])

    df = pd.merge(tracing, repositories, left_on='repo_id', right_on='id').drop(columns=['id', 'repo_id'])
    df = pd.merge(expected, df, left_on='id', right_on='method_id').drop(columns=['method_id'])

    # remove entries that are not satisfying the coverage criteria
    if coverage != 'none':
        df = df[df[f'{coverage}_coverage'] >= threshold]
    df = df.drop(columns=['instruction_coverage', 'line_coverage'])

    special_token = None
    if measure == 'token':
        special_token = ' '
    elif measure == 'line':
        special_token = '<NEW_LINE>'

    # remove entries that are not satisfying the measure criteria
    if special_token is not None:
        min_value = min_value if min_value else 0
        max_value = max_value if max_value else float('inf')

        df['code'] = df['code'].apply(lambda x: x.split(special_token))
        df = df[df['code'].apply(lambda x: min_value <= len(x) <= max_value)]
        df['code'] = df['code'].apply(lambda x: special_token.join(x))

    if eval_time:
        time_left = eval_time
        for row in df.itertuples():
            if row.time <= time_left:
                time_left -= row.time
            else:
                df = df.drop(index=row.Index)

    df = df.drop(columns=['time'])

    create_directory_if_needed(output_folder)
    df.to_csv(output_folder + '/dataset.csv', index=False)
