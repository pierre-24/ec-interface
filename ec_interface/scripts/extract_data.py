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

    g_analysis = parser.add_mutually_exclusive_group()
    g_analysis.add_argument('--pbm', action='store_true', help='Assume PBM approach')
    g_analysis.add_argument(
        '--hbm', type=float, help='Give the active fraction and assume HBM approach')
    g_analysis.add_argument(
        '--hbm-ideal', action='store_true', help='Compute the active fraction and assume the HBM approach')
    g_analysis.add_argument(
        '--hbm-fermi', action='store_true', help='Assume the HBM approach, but use the Fermi energy for work function')

    args = parser.parse_args()

    def _outverb(*args_, **kwargs):
        if args.verbose:
            print(*args_, **kwargs)

    # get parameters
    ec_input_file = args.directory / INPUT_NAME
    if not ec_input_file.exists():
        raise FileNotFoundError('file `{}` does not exists'.format(ec_input_file))

    with ec_input_file.open() as f:
        ec_parameters = ECParameters.from_yaml(f)

    # extract data
    ec_results = ECResults.from_calculations(ec_parameters, args.directory, verbose=args.verbose)

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
        'Work function [V]\t'
    )

    if args.pbm:
        args.output.write('Grand potential (PBM) [V]\n')
        numpy.savetxt(args.output, ec_results.compute_fee_pbm(), delimiter='\t')
        _outverb('Used PBM to estimate the FEE')
    elif args.hbm:
        args.output.write('Grand potential (HBM, alpha={:.4f}) [V]\n'.format(args.hbm))
        numpy.savetxt(args.output, ec_results.compute_fee_hbm(alpha=args.hbm), delimiter='\t')
        _outverb('Used HBM (alpha = {}) to estimate the FEE'.format(args.hbm))
    elif args.hbm_ideal:
        alpha = ec_results.estimate_active_fraction()
        args.output.write('Grand potential (HBM, alpha={:.4f}) [V]\n'.format(alpha))
        numpy.savetxt(args.output, ec_results.compute_fee_hbm(alpha=alpha), delimiter='\t')
        _outverb('Used HBM (alpha = {:.4f}) to estimate the FEE'.format(alpha))
    else:
        args.output.write('Grand potential (HBM, WF=Fermi) [V]\n')
        numpy.savetxt(args.output, ec_results.compute_fee_hbm_fermi(), delimiter='\t')
        _outverb('Used HBM (WF=Fermi) to estimate the FEE')

    args.output.close()


if __name__ == '__main__':
    main()
