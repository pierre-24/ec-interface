"""
Create directories for calculations
"""

import argparse
import pathlib
import sys

from ec_interface.ec_input import ECInput, ECInputError


def getdir(inp: str) -> pathlib.Path:
    directory = pathlib.Path(inp)
    if not directory.is_dir():
        raise argparse.ArgumentTypeError('`{}` is not a valid directory'.format(directory))

    return directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('directory', default='.', type=getdir)

    args = parser.parse_args()

    # check if files exists
    ec_input_file = args.directory / 'ec_interface.yml'
    incar_file = args.directory / 'INCAR'
    poscar_file = args.directory / 'POSCAR'
    potcar_file = args.directory / 'POTCAR'
    kpoints_file = args.directory / 'KPOINTS'

    # get ec input info
    try:
        if not ec_input_file.exists():
            raise ECInputError('missing `{}`!'.format(ec_input_file))

        ec_input = ECInput.from_yaml(ec_input_file.open())
        ec_input.create_directories(incar_file, poscar_file, potcar_file, kpoints_file)
    except ECInputError as e:
        print(e, file=sys.stderr)


if __name__ == '__main__':
    main()
