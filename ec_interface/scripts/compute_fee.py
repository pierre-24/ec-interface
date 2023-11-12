"""
Extract data form calculations
"""

import argparse
import numpy
import pathlib
import sys

from ec_interface.ec_results import ECResults
from ec_interface.scripts import get_ec_parameters


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-i', '--h5', default='ec_results.h5', help='H5 file')
    parser.add_argument('-o', '--output', default=sys.stdout, type=argparse.FileType('w'))
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose')

    g_analysis = parser.add_mutually_exclusive_group()
    g_analysis.add_argument('--pbm', action='store_true', help='Assume PBM approach')
    g_analysis.add_argument(
        '--hbm', type=float, help='Give the active fraction and assume HBM approach')
    g_analysis.add_argument(
        '--hbm-ideal', action='store_true', help='Compute the active fraction and assume the HBM approach')
    g_analysis.add_argument(
        '--hbm-fermi', action='store_true', help='Assume the HBM approach, but use the Fermi energy for work function')

    parser.add_argument('--shift', type=float, default=.0, help='Shift the vacuum potential')

    args = parser.parse_args()
    this_directory = pathlib.Path('.')

    # get parameters
    ec_parameters = get_ec_parameters(this_directory)

    # extract data
    ec_results = ECResults.from_hdf5(ec_parameters, args.h5, verbose=args.verbose)

    # write results
    args.output.write(
        'NELECT\t'
        'Free energy [eV]\t'
        'Fermi energy [eV]\t'
        'Vacuum potential [eV]\t'
        'Average potential [eV]\n'
    )

    numpy.savetxt(args.output, ec_results.data, delimiter='\t')

    args.output.write(
        '\n\n'  # just skip a few lines so that it is another dataset
        'Charge [e]\t'
        'Work function [V]{}\t'.format(' (shift={})'.format(args.shift) if args.shift != .0 else '')
    )

    if args.pbm:
        args.output.write('Grand potential (PBM) [V]\n')
        numpy.savetxt(args.output, ec_results.compute_fee_pbm(shift=args.shift), delimiter='\t')
    elif args.hbm:
        args.output.write('Grand potential (HBM, alpha={:.4f}) [V]\n'.format(args.hbm))
        numpy.savetxt(args.output, ec_results.compute_fee_hbm(alpha=args.hbm, shift=args.shift), delimiter='\t')
    elif args.hbm_ideal:
        alpha = ec_results.estimate_active_fraction(shift=args.shift)
        args.output.write('Grand potential (HBM, alpha={:.4f}) [V]\n'.format(alpha))
        numpy.savetxt(args.output, ec_results.compute_fee_hbm(alpha=alpha, shift=args.shift), delimiter='\t')
    else:
        args.output.write('Grand potential (HBM, WF=Fermi) [V]\n')
        numpy.savetxt(args.output, ec_results.compute_fee_hbm_fermi(shift=args.shift), delimiter='\t')

    args.output.close()


if __name__ == '__main__':
    main()
