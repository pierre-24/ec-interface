import argparse
import pathlib

INPUT_NAME = 'ec_interface.yml'


def get_directory(inp: str) -> pathlib.Path:
    directory = pathlib.Path(inp)
    if not directory.is_dir():
        raise argparse.ArgumentTypeError('`{}` is not a valid directory'.format(directory))

    return directory
