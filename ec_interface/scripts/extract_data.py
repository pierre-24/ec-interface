import argparse
import pathlib
import sys

from ec_interface.ec_parameters import ECParameters
from ec_interface.vasp_results import VaspResults
from ec_interface.scripts import get_directory, INPUT_NAME


def extract_data_from_directory(directory: pathlib.Path):
    """Extract the data from a calculation. Most of the results are obtained from `vaspout.h5`
    """

    path_h5 = directory / 'vaspout.h5'
    if not path_h5.exists():
        raise FileNotFoundError('file `{}` does not exists'.format(path_h5))

    data_h5 = VaspResults.from_h5(path_h5)


def extract_data_from_directories(directory: pathlib.Path):
    """Extract data from the directories where calculations were performed.
    """

    ec_input_file = directory / INPUT_NAME
    if not ec_input_file.exists():
        raise FileNotFoundError('file `{}` does not exists'.format(ec_input_file))

    with ec_input_file.open() as f:
        ec_parameters = ECParameters.from_yaml(f)

    for subdirectory in ec_parameters.directories(directory):
        if not subdirectory.exists():
            raise FileNotFoundError('directory `{}` does not exists'.format(subdirectory))

        extract_data_from_directory(subdirectory)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-i', '--directory', default='.', type=get_directory, help='Input directory')
    args = parser.parse_args()

    # extract data
    try:
        extract_data_from_directories(args.directory)
    except Exception as e:
        print('error:', e, file=sys.stderr)


if __name__ == '__main__':
    main()
