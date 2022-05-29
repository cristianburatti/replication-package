import os
import re
import argparse
from progress.bar import Bar
from git import Repo
from git.cmd import Git
from git.exc import GitCommandError
from utils.file_system import *
from utils.parsing import *
from utils.time import *
from datetime import datetime

timeout = 300  # seconds (= 5 minutes)


def initialize_df():
    df = parse_all_methods()
    df['SNAPSHOT'] = None
    df['VALID'] = True

    return df


def handle_java_repo(snapshots, repo, df, idx, repo_name):
    snapshot = snapshots.loc[repo_name, 'SNAPSHOT']
    df.loc[idx, 'SNAPSHOT'] = snapshot

    df = checkout(repo, df, idx)

    return df


def check_heuristic(df, idx):
    repo_name, file_name, code = df.loc[idx, 'REPO_NAME'], df.loc[idx, 'FILE_NAME'], df.loc[idx, 'CODE']
    code = code.replace('\\\\n', '\n')
    code = re.sub(r"\s+", " ", code).strip()

    save_folder = f'repo__{repo_name.replace("/", "_")}'

    with open(os.path.join(repos, save_folder, file_name), 'r') as f:
        content = f.read()
        content = re.sub(r"\s+", " ", content).strip()
        if code not in content:
            df.loc[idx, 'VALID'] = False

    return df


def handle_android_repo(repo, df, idx):
    log_info = repo.git.log('-n1', '--before="2020-02-25"', '--date=format:%Y-%m-%d %H:%M:%S')
    commit_id = log_info.split('\n')[0].split(' ')[1]
    df.loc[idx, 'SNAPSHOT'] = commit_id

    df = checkout(repo, df, idx)

    check_heuristic(df, idx)

    return df


def checkout(repo, df, idx):
    snapshot = df.loc[idx, 'SNAPSHOT']
    repo.git.checkout(snapshot)

    return df


def print_time(keyword):
    now = datetime.now()

    current_time = now.strftime("%H:%M:%S")
    print(f"{keyword}: {current_time}")
    return now


def main(options):
    start_at = print_time("Start time")
    create_repos()
    create_archives()

    failed_repos = parse_failed_repos()

    df = initialize_df()
    snapshots = parse_java_commits()
    results_name = 'all'

    if options.scope == 'range':
        df = df.iloc[options.start:options.end]
        results_name = f'range_{options.start}_{options.end}'
        print(f"Analyzing range of methods: {options.start} to {options.end}")
    elif options.scope == 'block':
        block_size = round(len(df) / options.total_blocks)
        start = options.block_number * block_size
        end = start + block_size
        df = df.iloc[start:end]
        results_name = f'block_{start}_{end}__{options.block_number}_{options.total_blocks}'
        print(f"Analyzing block of methods: {start} to {end}")

    rows = df.shape[0]
    count = 1
    bar = Bar('Processing', max=rows)

    for idx, row in df.iterrows():
        repo_name, dataset = row['REPO_NAME'], row['DATASET']
        url = f'https://www.github.com/{repo_name}'

        save_folder = f'repo__{repo_name.replace("/", "_")}'
        bar.suffix = f'{count}/{rows} ({float(count) / float(rows) * 100:.2f}%%) | {elapsed_time(start_at)} | {repo_name}'

        if save_folder in os.listdir(repos) or f'{save_folder}.zip' in os.listdir(archives):
            count += 1
            bar.next()
            continue

        if repo_name in failed_repos:
            count += 1
            bar.next()
            df.loc[idx, 'VALID'] = False
            continue

        try:
            g = Git(os.path.join(repos, save_folder))
            g.clone(Git.polish_url(url), os.path.join(repos, save_folder), kill_after_timeout=timeout)
            repo = Repo.init(os.path.join(repos, save_folder))

            if dataset == 'java':
                df = handle_java_repo(snapshots, repo, df, idx, repo_name)
            else:
                df = handle_android_repo(repo, df, idx)

            zip_repo(save_folder)
        except (GitCommandError, KeyError, FileNotFoundError, UnicodeError, IndexError):
            failed_repos.add(repo_name)
            df.loc[idx, 'VALID'] = False
        except Exception as e:
            print(e)
            failed_repos.add(repo_name)
            df.loc[idx, 'VALID'] = False
        finally:
            count += 1
            bar.next()
            delete_repo(save_folder)
    bar.finish()
    out_csv(df, results_name)
    out_failed(failed_repos, results_name)
    print_time("End time")


def handle_cl_args():
    parser = argparse.ArgumentParser()

    parser.add_argument('--scope', type=str, default='all', choices=['all', 'block', 'range'],
                        help='Scope of the analysis')
    parser.add_argument_group('block', 'Block of methods to analyze')

    block_group = parser.add_argument_group('block', 'Block of methods to analyze')
    block_group.add_argument('--block_number', type=int, help="Number of the block (from 0 to total_blocks - 1)")
    block_group.add_argument('--total_blocks', type=int, help="Total number of blocks")

    range_group = parser.add_argument_group('range', 'Range of methods to analyze')
    range_group.add_argument('--start', type=int, help='Start index (inclusive)')
    range_group.add_argument('--end', type=int, help='End index (exclusive)')

    options = parser.parse_args()
    return parser, options


if __name__ == '__main__':
    out, args = handle_cl_args()

    if args.scope == 'range':
        if args.start is None or args.end is None:
            out.error("--scope 'range' requires --from and --to.")
        elif args.start >= args.end or args.start < 0 or args.end < 0:
            out.error("--from must be smaller than --to and both must be greater than 0.")
    elif args.scope == 'block':
        if args.block_number is None or args.total_blocks is None:
            out.error("--scope 'block' requires --block_number and --total_blocks.")
        elif args.block_number >= args.total_blocks or args.total_blocks <= 0:
            out.error("--block_number must be smaller than --total_blocks and the latter must be greater than 0.")

    main(args)
