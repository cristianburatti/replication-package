import os
import shutil


class UnzippableError(Exception):
    pass


def reformat_repo_name(repo_name):
    """
    Reformat the repo name to be compatible with the file system
    Example: "google/guava" -> "repo__google_guava"
    :param repo_name: the repo name to reformat
    :return: the reformatted repo name
    """

    return f'repo__{repo_name.replace("/", "_")}'


def create_directory_if_needed(directory):
    """
    Create a directory iff it does not exist
    :param directory: the directory to create
    """

    if not os.path.exists(directory):
        os.makedirs(directory)


def delete_dir(directory):
    """
    Delete a directory iff it exists
    :param directory: the directory to delete
    """

    if os.path.exists(directory):
        # ignoring errors as it will eventually be deleted at the end of the program
        shutil.rmtree(directory, ignore_errors=True)


def create_working_environment():
    delete_dir('resources')
    delete_dir('tmp_mine')
    create_directory_if_needed('resources')
    create_directory_if_needed(f'tmp_mine')


def zip_dir(repo_name):
    """
    Remove the .git folder, zip the directory and move it to the output directory
    :param repo_name: the repo name
    :raise UnzippableError: if the directory contains timestamps before the 1980s and is therefore unzippable
    """

    delete_dir(os.path.join(f'tmp_mine', repo_name, '.git'))
    try:
        shutil.make_archive(os.path.join('resources', repo_name), 'zip', f'tmp_mine', repo_name)
    except ValueError:
        raise UnzippableError()


def unzip_dir(repo_name):
    """
    Unzip a mined directory
    :param repo_name: the formatted name of the repo to unzip
    """

    shutil.unpack_archive(f'resources/{repo_name}.zip', 'tmp_evaluate', 'zip')
