from zipfile import ZipFile
import os
import shutil

cache = []
CACHE_SIZE = 5


def delete_directory(path):
    if os.path.exists(path):
        shutil.rmtree(path)


def conventional_name(repository):
    return f'repo__{repository.replace("/", "_")}'


def repository_to_path(data_path, repository):
    return os.path.join(data_path, 'archives', f'{repository}.zip')


def extract_file_content(data_path, tmp_path, repository, file_name):
    repository_real_name = conventional_name(repository)
    if repository_real_name not in cache:
        if len(cache) == CACHE_SIZE:
            delete_directory(os.path.join(tmp_path, cache.pop(0)))
        cache.append(repository_real_name)
        with ZipFile(repository_to_path(data_path, repository_real_name), 'r') as f:
            f.extractall(tmp_path)

    try:
        with open(os.path.join(tmp_path, repository_real_name, file_name), 'r') as f:
            data = f.read()
    except (FileNotFoundError, UnicodeError):
        data = ''

    return data
