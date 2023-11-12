"""
Extract data form calculations
"""

import argparse
import pathlib

from ec_interface.ec_results import ECResults
from ec_interface.scripts import get_ec_parameters


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-o', '--output', default='ec_results.h5')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose')

    args = parser.parse_args()
    this_directory = pathlib.Path('.')

    # get parameters
    ec_parameters = get_ec_parameters(this_directory)

    # extract data
    ec_results = ECResults.from_calculations(ec_parameters, this_directory, verbose=args.verbose)

    # write results
    ec_results.to_hdf5(pathlib.Path(args.output))


if __name__ == '__main__':
    main()
