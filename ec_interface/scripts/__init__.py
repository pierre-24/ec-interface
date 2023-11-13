import argparse
import pathlib

from ec_interface.ec_parameters import ECParameters

INPUT_NAME = 'ec_interface.yml'
H5_NAME = 'ec_results.h5'


def assert_exists(p: pathlib.Path):
    if not p.exists():
        raise FileNotFoundError('file `{}` does not exists'.format(p))

    return p


def get_directory(inp: str) -> pathlib.Path:
    directory = pathlib.Path(inp)
    if not directory.is_dir():
        raise argparse.ArgumentTypeError('`{}` is not a valid directory'.format(directory))

    return directory


def get_ec_parameters(fp: str) -> ECParameters:
    p = pathlib.Path(fp)
    if not p.exists():
        raise argparse.ArgumentTypeError('`{}` does not exists'.format(fp))

    with p.open() as f:
        return ECParameters.from_yaml(f)
