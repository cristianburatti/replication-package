import os
import nltk
import numpy as np
from multiprocessing import Process
from utils.timer import run_with_timer
from utils.file_system import unzip_dir, delete_dir
from mine_utils.compilation import compile_mvn_project, compile_gradle_project


def accuracy(target: str, predicted: str):
    """
    Calculate the accuracy of the prediction.
    :param target: the expected code
    :param predicted: the predicted code
    :return: whether the prediction and the expected code are the same (without whitespaces)
    """

    return ''.join(target.split()) == ''.join(predicted.split())


def bleu_score(target: str, predicted: str, preferred_score: str):
    """
    Calculate the BLEU score between the target and the predicted code.
    :param target: the expected code
    :param predicted: the predicted code
    :param preferred_score: the preferred score to calculate (1, 2, 3, 4 or avg [default avg])
    :return: the BLEU score between the two strings
    """

    # computes the BLEU_n score
    def n_score(n):
        if n > 1 and len(target_list) < n:
            return None
        if is_perfect_prediction:
            return 1.0

        weights = [(1.0, 0.0), (0.5, 0.5, 0.0), (0.333, 0.333, 0.333), (0.25, 0.25, 0.25, 0.25)]
        return nltk.translate.bleu_score.sentence_bleu(target_list, predicted_list, weights=weights[n - 1])

    target_list = target.split()
    predicted_list = predicted.split()
    is_perfect_prediction = ''.join(target_list) == ''.join(predicted_list)

    if preferred_score == 'avg':
        scores = [n_score(n) for n in range(1, 5)]
        return np.mean([s for s in scores if s is not None])
    else:
        return n_score(int(preferred_score))


def levenshtein_distance(target: str, predicted: str):
    """
    Calculate the Levenshtein distance between the target and the predicted code.
    :param target: the expected code
    :param predicted: the predicted code
    :return: the Levenshtein distance between the two strings
    """

    seq_x = target.split()
    seq_y = predicted.split()

    size_x = len(seq_x) + 1
    size_y = len(seq_y) + 1
    matrix = np.zeros((size_x, size_y))

    for x in range(size_x):
        matrix[x, 0] = x
    for y in range(size_y):
        matrix[0, y] = y

    for x in range(1, size_x):
        for y in range(1, size_y):
            if seq_x[x - 1] == seq_y[y - 1]:
                matrix[x, y] = min(
                    matrix[x - 1, y] + 1,
                    matrix[x - 1, y - 1],
                    matrix[x, y - 1] + 1
                )
            else:
                matrix[x, y] = min(
                    matrix[x - 1, y] + 1,
                    matrix[x - 1, y - 1] + 1,
                    matrix[x, y - 1] + 1
                )

    return matrix[size_x - 1, size_y - 1] / max(size_x, size_y)


def integrity(repo_name, root, file, start, end, predicted_code, project, max_time):
    """
    Calculate the integrity of the prediction, i.e. whether the predicted code can replace the original code without
    breaking the tests of the project
    :param repo_name: the name of the project
    :param root: the root of the project
    :param file: the path of the java file inside the root of the project
    :param start: the start line of the original code
    :param end: the end line of the original code
    :param predicted_code: the predicted code
    :param project: the type of the project (mvn or gradle)
    :param max_time: the time it took the first time to build the project
    :return: a tuple of boolean:
        - first element: integrity of the project (True if the tests passed, False otherwise)
        - second element: success of the task (True if the task ended in time, False if it timed out)
    """

    unzip_dir(repo_name)
    working_dir = os.path.join('tmp_evaluate', repo_name, root)
    file_path = os.path.join(working_dir, file)

    # replace the original code with the predicted code
    with open(file_path, 'r') as f:
        lines = f.readlines()
    content = ''.join(lines[:start] + [predicted_code] + lines[end:])
    with open(file_path, 'w') as f:
        f.write(content)

    # build the project allowing for an extra 10% of time
    timeout = 60 + max_time * 1.1
    if project == 'mvn':
        target = compile_mvn_project
    else:
        target = compile_gradle_project

    completed, success, _ = run_with_timer(target=target, args=working_dir, timeout=timeout)
    delete_dir('tmp_evaluate')

    return completed, success
