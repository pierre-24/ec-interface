"""
Extract data form calculations
"""

import argparse
import numpy

from ec_interface.ec_parameters import ECParameters
from ec_interface.ec_results import ECResults
from ec_interface.scripts import get_directory, INPUT_NAME


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-i', '--directory', default='.', type=get_directory, help='Input directory')
    parser.add_argument('-o', '--output', default='ec_results.csv', type=argparse.FileType('w'))
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose')

    args = parser.parse_args()

    # get parameters
    ec_input_file = args.directory / INPUT_NAME
    if not ec_input_file.exists():
        raise FileNotFoundError('file `{}` does not exists'.format(ec_input_file))

    with ec_input_file.open() as f:
        ec_parameters = ECParameters.from_yaml(f)

    # extract data
    ec_results = ECResults(ec_parameters, args.directory, verbose=args.verbose)

    # write results
    args.output.write(
        'NELECT\t'
        'Free energy [eV]\t'
        'Fermi energy [eV]\t'
        'Vacuum potential [eV]\t'
        'Average potential [eV]\n'
    )

    dataframe = numpy.array([
        ec_results.nelects,
        ec_results.free_energies,
        ec_results.vacuum_potentials,
        ec_results.average_potentials
    ])

    numpy.savetxt(args.output, dataframe.T, delimiter='\t')

    args.output.write(
        '\n'
        'Charge [e]\t'
        'Work function [V]\t'
        'Grand potential [V]\n'
    )

    ec_results.estimate_active_fraction()

    args.output.close()


if __name__ == '__main__':
    main()
