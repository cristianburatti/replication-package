from git import Repo
from git.cmd import Git
from mine_utils.mine_exceptions import MissingTagException


def clone_repository(name: str, save_folder: str):
    """
    Clone a GitHub repository into a local folder
    :param name: the name of the repository
    :param save_folder: the folder to save the repository
    :return: the cloned repository object
    """

    url = f'https://www.github.com/{name}'

    g = Git(save_folder)
    timeout = 300  # 300 seconds (5 minutes)

    g.clone(Git.polish_url(url), save_folder, kill_after_timeout=timeout)
    repo = Repo.init(save_folder)

    return repo


def extract_tag(repo: Repo, log):
    """
    Extract the latest snapshot/tag from the repository and checkout it
    :param repo: The cloned repo object
    :param log: The logger function
    :raise: MissingTagException if no tag is found
    :return: The tag name
    """

    tags = repo.tags

    try:
        tags.sort(key=lambda t: t.commit.committed_datetime)
        tag = tags[-1]

        repo.git.checkout(f'tags/{tag}')
    except (ValueError, IndexError):
        log(f'N/A,N/A,', file='repositories')  # log N/A for tag and project
        raise MissingTagException()

    return tag
