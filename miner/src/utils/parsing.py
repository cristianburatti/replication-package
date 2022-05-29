import pandas as pd


def parse_failed_repos():
    with open('in/failed.txt', 'r') as f:
        repos = f.read().split('\n')
        repos = set(repos)
        return repos


def parse_all_methods():
    with open('data/finetuning/all_methods.txt', 'r') as f:
        lines = f.readlines()
        headers = lines[0][:-1].split("\t")
        lines = [line[:-1].split("\t") for line in lines[1:]]

        df = pd.DataFrame(lines, columns=headers)
        column_names = ['ID', 'ignore', 'CODE', 'DATASET', 'REPO_NAME', 'FILE_NAME']
        df = df.rename(columns={
            x: y for x, y in list(zip(headers, column_names))
        })
        df = df.drop(columns=['ignore'])

        return df


def parse_java_commits():
    with open('data/finetuning/java_repository_commit.txt', 'r') as f:
        lines = f.read().split('\n')
        lines = [line.split(',') for line in lines]
        df = pd.DataFrame(lines, columns=['REPO_NAME', 'SNAPSHOT'])
        df = df.set_index('REPO_NAME')
        return df
