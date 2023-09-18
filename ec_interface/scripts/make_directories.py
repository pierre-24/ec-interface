"""
Create directories for calculations
"""

import argparse
import pathlib
import sys

from ec_interface.ec_parameters import ECParameters


def getdir(inp: str) -> pathlib.Path:
    directory = pathlib.Path(inp)
    if not directory.is_dir():
        raise argparse.ArgumentTypeError('`{}` is not a valid directory'.format(directory))

    return directory


def create_input_directories(directory: pathlib.Path):
    """Create directories containing input files, ready to compute
    """

    def assert_exists(p: pathlib.Path):
        if not p.exists():
            raise FileNotFoundError('file `{}` does not exists'.format(p))

        return p

    ec_input_file = assert_exists(directory / 'ec_interface.yml')
    incar_file = assert_exists(directory / 'INCAR')
    poscar_file = assert_exists(directory / 'POSCAR')
    potcar_file = assert_exists(directory / 'POTCAR')
    kpoints_file = assert_exists(directory / 'KPOINTS')

    # check that file exist
    assert_exists(ec_input_file)
    assert_exists(incar_file)
    assert_exists(poscar_file)
    assert_exists(potcar_file)
    assert_exists(kpoints_file)

    # get params
    ec_parameters = ECParameters.from_yaml(ec_input_file.open())

    incar_content = incar_file.open().read()
    # TODO: check INCAR!

    # create subdirs
    for n in ec_parameters.steps():
        subdirectory = directory / '{}_{:.3f}'.format(ec_parameters.prefix, n)
        subdirectory.mkdir()

        # copy INCAR
        with (subdirectory / 'INCAR').open('w') as f:
            f.write(incar_content)
            f.write('\n! EC calculation\nNELECT = {:.3f}'.format(n))

        # create symlinks for other files
        for p in ['POSCAR', 'POTCAR', 'KPOINTS']:
            (subdirectory / p).symlink_to('../{}'.format(p))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-i', '--directory', default='.', type=getdir, help='Input directory')
    args = parser.parse_args()

    # get ec input info
    try:
        create_input_directories(args.directory)
    except Exception as e:
        print('error:', e, file=sys.stderr)


if __name__ == '__main__':
    main()
