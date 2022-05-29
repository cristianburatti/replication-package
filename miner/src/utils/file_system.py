import os
import shutil

repos = 'repos'
archives = 'archives'


def create_directory_if_needed(path):
    if not os.path.exists(path):
        os.makedirs(path)


def create_repos():
    create_directory_if_needed(repos)


def create_archives():
    create_directory_if_needed(archives)


def zip_repo(directory):
    git_directory = os.path.join(repos, directory, '.git')
    try:
        shutil.rmtree(git_directory)
    except FileNotFoundError:
        pass

    shutil.make_archive(os.path.join(archives, directory), 'zip', repos, directory)


def delete_repo(directory):
    if os.path.exists(os.path.join(repos, directory)):
        shutil.rmtree(os.path.join(repos, directory))


def out_csv(df, filename):
    out_path = 'out'
    create_directory_if_needed(out_path)
    df.to_csv(os.path.join(out_path, f'{filename}.csv'), index=False)


def out_failed(failed_repos, results_name):
    ordered_repos = list(failed_repos)
    ordered_repos = [x for x in ordered_repos if x != '']
    ordered_repos.sort()
    with open(os.path.join('out', f'failed_repos_{results_name}.txt'), 'w') as f:
        for repo in ordered_repos:
            f.write(f'{repo}\n')
