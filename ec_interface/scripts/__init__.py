import argparse
import pathlib

import numpy
from numpy._typing import NDArray

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


def get_lattice(inp: str) -> NDArray:
    elmts = inp.split(',')
    if len(elmts) != 3:
        raise argparse.ArgumentTypeError('Lattice must have three elements')

    lattice = numpy.zeros((3, 3))
    for i in range(3):
        try:
            lattice[i, i] = float(elmts[i])
        except ValueError:
            raise argparse.ArgumentTypeError('Element {} of lattice is not a float'.format(i))

    return lattice


def get_vec(inp: str) -> NDArray:
    elmts = inp.split(',')
    if len(elmts) != 3:
        raise argparse.ArgumentTypeError('COM shift must have three elements')

    try:
        return numpy.array([float(x) for x in elmts])
    except ValueError:
        raise argparse.ArgumentTypeError('COM shift must be 3 floats')
