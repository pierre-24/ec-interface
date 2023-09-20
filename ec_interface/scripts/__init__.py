import argparse
import pathlib

INPUT_NAME = 'ec_interface.yml'


def assert_exists(p: pathlib.Path):
    if not p.exists():
        raise FileNotFoundError('file `{}` does not exists'.format(p))

    return p


def get_directory(inp: str) -> pathlib.Path:
    directory = pathlib.Path(inp)
    if not directory.is_dir():
        raise argparse.ArgumentTypeError('`{}` is not a valid directory'.format(directory))

    return directory
