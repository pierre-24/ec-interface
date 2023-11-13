"""
Extract data form calculations
"""

import argparse
import pathlib

from ec_interface.ec_results import ECResults
from ec_interface.scripts import get_ec_parameters, INPUT_NAME, H5_NAME


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-p', '--parameters', default=INPUT_NAME, type=get_ec_parameters)
    parser.add_argument('-o', '--output', default=H5_NAME)
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose')

    args = parser.parse_args()
    this_directory = pathlib.Path('.')

    # extract data
    ec_results = ECResults.from_calculations(args.parameters, this_directory, verbose=args.verbose)

    # write results
    ec_results.to_hdf5(pathlib.Path(args.output))


if __name__ == '__main__':
    main()
