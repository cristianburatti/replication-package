import os
import re
import pandas as pd
from javalang.tokenizer import LexerError
from javalang.parser import JavaSyntaxError
from context.context import extract_file_content, delete_directory
from context.classes import extractor_factory, ExtractorError, Extractors
from context.dataset import Dataset
from utils.time import *
from utils.parsing import *
from utils.cli import CLI
from utils.file_system import create_directory_if_needed
from datetime import datetime
from progress.bar import Bar


def flatten(string):
    string = string.strip()
    string = string.replace('\n', ' ')
    string = string.replace('\\n', ' ')
    string = string.replace('\t', ' ')
    string = string.replace('\\t', ' ')
    string = re.sub('\\s+', ' ', string)
    return string


def collect_data(base_path):
    tracing = parse_tracing(base_path)
    masked_code = parse_masked_code(base_path)
    mask = parse_mask(base_path)

    entries = min(len(tracing), len(masked_code), len(mask))

    return [[tracing[i], masked_code[i], mask[i]] for i in range(entries)]


def conventional_tsv_name(folder):
    dataset, level, scope = folder.split('_')
    scope = scope.replace('training', 'train')
    return scope + '_' + dataset + '_' + level + '.tsv'


def main():
    args = CLI()
    extractor = extractor_factory(args.extractor)
    javadoc_extractor = extractor_factory(Extractors.javadoc)

    delete_directory(args.tmp)
    create_directory_if_needed(args.tmp)
    create_directory_if_needed('out')

    df = pd.read_csv(os.path.join(args.data, 'main.csv'))
    df = df.set_index('ID')

    for folder in args.folders:
        base_path = os.path.join(args.data, folder)
        tsv_name = conventional_tsv_name(folder)

        data = collect_data(base_path)

        count = 1
        total = len(data)

        bar = Bar('Processing ' + tsv_name.ljust(27), max=total)
        start_at = datetime.now()

        baseline_count = 0
        written_data = 0

        with open(os.path.join('out', tsv_name), 'w') as f:
            for method_id, masked_code, mask in data:
                count_str = f'{count}/{total} ({float(count) / float(total) * 100:.2f}%%)'
                bar.suffix = f'{count_str} | {elapsed_time(start_at)} | {baseline_count} | {written_data}'
                row = df.loc[method_id]

                if row['VALID']:
                    flatten_masked_code = flatten(masked_code.replace('<x>', '<extra_id_0>'))
                    flatten_mask = flatten(mask.replace('<z>', ''))

                    file_content = None
                    if extractor.needs_file_content():
                        file_content = extract_file_content(args.data, args.tmp, row['REPO_NAME'], row['FILE_NAME'])

                    if args.dataset == Dataset.complete:
                        try:
                            context = flatten(extractor.extract(flatten_masked_code, flatten_mask, file_content))
                        except (ExtractorError, LexerError, JavaSyntaxError, RecursionError, IndexError):
                            baseline_count += 1
                            context = extractor.baseline()
                        except Exception as e:
                            print(e)
                            baseline_count += 1
                            context = extractor.baseline()

                        f.write(f'{flatten_masked_code} {context}\t{flatten_mask}\n')
                        written_data += 1
                    else:  # javadoc dataset
                        try:
                            context = javadoc_extractor.extract(flatten_masked_code, flatten_mask, file_content)
                            if extractor.value != Extractors.javadoc:
                                context = extractor.extract(flatten_masked_code, flatten_mask, file_content)
                            context = flatten(context)
                            f.write(f'{method_id}\t{flatten_masked_code} {context}\t{flatten_mask}\n')
                            written_data += 1
                        except (ExtractorError, LexerError, JavaSyntaxError, RecursionError, IndexError):
                            pass
                        except Exception as e:
                            print(e)
                            pass
                count += 1
                bar.next()

        bar.finish()
    delete_directory(args.tmp)


if __name__ == '__main__':
    main()
