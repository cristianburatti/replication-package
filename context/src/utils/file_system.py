import os
import shutil


def create_directory_if_needed(path):
    if not os.path.exists(path):
        os.makedirs(path)
