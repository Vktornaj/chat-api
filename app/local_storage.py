import os
import shutil
import glob
from pathlib import Path


def save_file(path_file: str, file: bytes):
    filename = path_file.split("/")[-1]
    path = path_file.replace(filename, '')
    Path(path).mkdir(parents=True, exist_ok=True)
    with open(path_file, "wb") as f:
        f.write(file)


def get_file(path_file):
    with open(path_file, mode='rb') as file:
        fileContent = file.read()
    return fileContent


def delete_file(file_path: str):
    os.remove(file_path)


def list_files(dir_path: str):
    dir_path = os.path.join(dir_path, "**", "*.*")
    yield from glob.glob(dir_path, recursive=True)


def delete_dir(dir_path: str):
    shutil.rmtree(dir_path)
