"""
Create directories for calculations
"""

import argparse
import pathlib
import re
import shutil
import sys

from ec_interface.scripts import INPUT_NAME, get_directory, assert_exists
from ec_interface.ec_parameters import ECParameters


def create_input_directories(directory: pathlib.Path, use_symlinks: bool = True):
    """Create directories containing input files, ready to compute
    """

    ec_input_file = assert_exists(directory / INPUT_NAME)
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
    with ec_input_file.open() as f:
        ec_parameters = ECParameters.from_yaml(f)

    # get INCAR and check content
    incar_content = incar_file.open().read()
    to_find = ['LCHARG', 'LVHAR', 'LVTOT']
    for keyword in to_find:
        if not re.compile(r'{}\s*=\s*\.TRUE\.'.format(keyword)).search(incar_content):
            raise Exception('cannot find `{} = .TRUE.` in INCAR'.format(keyword))

    if re.compile(r'NELECT\s*=\s*[0-9]*').search(incar_content):
        print('Warning: found `NELECT` in INCAR.')

    # create subdirs
    for n, subdirectory in zip(ec_parameters.steps(), ec_parameters.directories(directory)):
        subdirectory.mkdir()

        # copy INCAR
        with (subdirectory / 'INCAR').open('w') as f:
            f.write(incar_content)
            f.write('\n! EC calculation\nNELECT = {:.3f}'.format(n))

        # create symlinks/copy other files
        for p in ['POSCAR', 'POTCAR', 'KPOINTS']:
            if use_symlinks:
                (subdirectory / p).symlink_to('../{}'.format(p))
            else:
                shutil.copy(p, subdirectory / p)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-i', '--directory', default='.', type=get_directory, help='Input directory')
    parser.add_argument('-c', '--copy-files', action='store_true', help='Copy files instead of using symlinks')
    args = parser.parse_args()

    # get ec input info
    try:
        create_input_directories(args.directory, use_symlinks=not args.copy_files)
    except Exception as e:
        print('error:', e, file=sys.stderr)


if __name__ == '__main__':
    main()
