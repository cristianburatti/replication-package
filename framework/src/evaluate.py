import re
import sys
import numpy as np
import pandas as pd
from datetime import datetime
from metrics import accuracy, bleu_score, levenshtein_distance, integrity
from utils.file_system import reformat_repo_name, create_directory_if_needed
from utils.progress_bar import ProgressBar


def parse_predictions(predictions_path):
    """
    Ensures that the predictions are in the correct format and returns a dataframe with the following columns:
        - id: the id of the prediction
        - predicted_method: the predicted method as a whole
        - masked_code: the code that was masked by the user
        - predicted_code: the code that was predicted by the model
    :param predictions_path: the path to the predictions CSV file
    :return: a dataframe with the following columns: id, predicted_method, masked_code, predicted_code
    """

    df = pd.read_csv(predictions_path).fillna('null')
    if set(df.columns.tolist()) != {'id', 'predicted_method', 'masked_code', 'predicted_code'}:
        print(
            "Invalid predictions file: please provide a CSV with the following columns:\n"
            "\tid\n"
            "\tpredicted_method\n"
            "\tmasked_code\n"
            "\tpredicted_code\n",
            file=sys.stderr,
        )
        exit(1)

    return df


def clean(string):
    """
    Removes all <NEW_LINE> tokens and cleans the string from excess whitespaces
    :param string: the string to clean
    :return: the cleaned string
    """

    return re.sub(r'\s+', ' ', string.strip().replace('<NEW_LINE>', ' '))


def log(data, file_path, mode='w'):
    """
    Writes the data to the file at the given path
    :param data: the data to write
    :param file_path: the path to the file
    :param mode: the mode to open the file in (default: 'w')
    """

    with open(file_path, mode) as file:
        file.write(data)


def print_results(results, output_folder, len_results):
    """
    Prints the summary of the results to the console and to the output file
    :param results: the results object to process and print
    :param output_folder: the path to the output folder
    :param len_results: how many entries have been processed
    """

    def total(key, len_data):
        # creates entry for metrics that are a percentage (count), such as 'accuracy', 'integrity' and 'timeout'
        if len_data == 0:
            return f'  0.00% (0 / 0)'
        percentage = f'{results[key] / len_data * 100:.2f}'
        return f'{percentage.rjust(6)}% ({results[key]} / {len_data})'

    def statistic(key):
        # creates entry for metrics that are a distribution (mead, median), such as 'BLEU' and 'Levenshtein'
        return f"mean: {np.mean(results[key]):.2f}, median: {np.median(results[key]):.2f}"

    if len_results == 0:
        message = "No predictions to evaluate"
    else:
        message = \
            f"Terminated evaluation of the model.\n" \
            f"\tAccuracy:             {total('accuracy', len_results)}\n" \
            f"\tBLEU Score:           {statistic('bleu')}\n" \
            f"\tLevenshtein Distance: {statistic('levenshtein')}\n" \
            f"\tTest Integrity:       {total('integrity', len_results - results['timeout'])}\n" \
            f"\tTimeout:              {total('timeout', len_results)}\n"

    print(message)
    log(message, output_folder + '/summary.txt')
    log('\n'.join([str(x) for x in results['bleu']]), output_folder + '/bleu_distribution.txt')
    log('\n'.join([str(x) for x in results['levenshtein']]), output_folder + '/levenshtein_distribution.txt')


def evaluate(predictions_path, output_folder, preferred_n_gram):
    """
    Evaluates the predictions file by computing the following metrics:
        - accuracy
        - BLEU score
        - Levenshtein distance
        - test integrity, as in the number predictions that pass the tests out of all the entries that did not time out
        - timeout, as in the number of predictions that timed out before the end of the test
    :param predictions_path: the path to the predictions file
    :param output_folder: where the results should be written to
    :param preferred_n_gram: the n-gram to use for the BLEU score (1, 2 or 3, 4 or avg [default avg])
    """

    results = {
        'accuracy': 0,
        'bleu': [],
        'levenshtein': [],
        'integrity': 0,
        'timeout': 0
    }

    create_directory_if_needed(output_folder)

    # predicted columns: id, predicted_method, masked_code, predicted_code
    predicted = parse_predictions(predictions_path)

    # repositories columns: name, tag, project, root, status, time
    repositories = pd.read_csv("resources/repositories.csv").set_index("id").fillna('')

    # tracing columns: repo_id, file, start, end, instruction_coverage, line_coverage
    tracing = pd.read_csv("resources/tracing.csv").set_index("method_id")

    predicted = predicted.join(tracing, on='id', how='inner')

    log('id,accuracy,bleu_score,levenshtein_distance,tests_passed,timeout\n', output_folder + '/log.csv', 'w')

    bar = ProgressBar(predicted)
    for row in predicted.itertuples():
        bar.update(f'{row.id}', datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        bar.next()

        # collect data
        predicted_method = clean(row.predicted_method)
        target_code, predicted_code = clean(row.masked_code), clean(row.predicted_code)
        file, start, end = row.file, row.start, row.end

        repo = repositories.loc[row.repo_id]
        repo_name = reformat_repo_name(repo['name'])
        root, project, time = repo['root'], repo['project'], repo['time']

        # compute metrics
        computed_accuracy = accuracy(target_code, predicted_code)
        computed_bleu = bleu_score(target_code, predicted_code, preferred_n_gram)
        computed_levenshtein = levenshtein_distance(target_code, predicted_code)
        if computed_accuracy:
            completed, success = True, True
        else:
            completed, success = integrity(repo_name, root, file, start, end, predicted_method, project, time)

        # write to file
        log_message = f'{row.id},{computed_accuracy},{computed_bleu},{computed_levenshtein},{success},{not completed}\n'
        log(log_message, output_folder + '/log.csv', 'a')

        # update results
        results['accuracy'] += computed_accuracy
        results['bleu'].append(computed_bleu)
        results['levenshtein'].append(computed_levenshtein)
        if completed:
            results['integrity'] += success
        else:
            results['timeout'] += 1

    results['bleu'] = [x for x in results['bleu'] if x is not None]

    print_results(results, output_folder, len(predicted))
    bar.finish()
