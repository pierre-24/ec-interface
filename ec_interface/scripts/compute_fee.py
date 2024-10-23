"""
Extract data form calculations
"""

import argparse
import numpy
import sys

from ec_interface.ec_results import ECResults
from ec_interface.scripts import get_ec_parameters, INPUT_NAME, H5_NAME


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-p', '--parameters', default=INPUT_NAME, type=get_ec_parameters)
    parser.add_argument('-i', '--h5', default=H5_NAME, help='H5 file')
    parser.add_argument('-o', '--output', default=sys.stdout, type=argparse.FileType('w'))
    parser.add_argument('-r', '--ref', default=4.5, type=float, help='Reference value')

    g_analysis = parser.add_mutually_exclusive_group()
    g_analysis.add_argument('--pbm', action='store_true', help='Assume PBM approach')
    g_analysis.add_argument(
        '--hbm', type=float, help='Give the active fraction and assume HBM approach')
    g_analysis.add_argument(
        '--hbm-ideal', action='store_true', help='Compute the active fraction and assume the HBM approach')
    g_analysis.add_argument(
        '--hbm-fermi', action='store_true', help='Assume the HBM approach, but use the Fermi energy for work function')

    parser.add_argument('--shift-avg', action='store_true', help='Shift the FEE with the average potential at PZC')

    args = parser.parse_args()

    # extract data
    ec_results = ECResults.from_hdf5(args.parameters.ne_zc, args.h5)

    # just show the data found in the H5 file
    args.output.write(
        'NELECT\t'
        'Free energy [eV]\t'
        'Fermi energy [eV]\t'
        'Vacuum potential [eV]\t'
        'Average potential [eV]\n'
    )

    numpy.savetxt(args.output, ec_results.data, delimiter='\t')

    # Compute FEE:
    args.output.write(
        '\n\n'  # just skip a few lines so that it is another dataset
        'Charge [e]\t'
        'Work function{} [V]\t'.format(' (shifted with vacuum)' if args.shift_avg else '') + \
        'Potential vs ref [V]\t'
    )

    if args.pbm:
        args.output.write('Grand potential (PBM) [V]\n')
        results = ec_results.compute_fee_pbm(shift_with_avg=args.shift_avg, ref=args.ref)
        numpy.savetxt(args.output, results, delimiter='\t')
    elif args.hbm:
        args.output.write('Grand potential (HBM, alpha={:.4f}) [V]\n'.format(args.hbm))
        results = ec_results.compute_fee_hbm(alpha=args.hbm, shift_with_avg=args.shift_avg, ref=args.ref)
        numpy.savetxt(args.output, results, delimiter='\t')
    elif args.hbm_ideal:
        alpha = ec_results.estimate_active_fraction(shift_with_avg=args.shift_avg)
        args.output.write('Grand potential (HBM, alpha={:.4f}) [V]\n'.format(alpha))
        results = ec_results.compute_fee_hbm(alpha=alpha, shift_with_avg=args.shift_avg, ref=args.ref)
        numpy.savetxt(args.output, results, delimiter='\t')
    else:
        args.output.write('Grand potential (HBM, WF=Fermi) [V]\n')
        results = ec_results.compute_fee_hbm_fermi(shift_with_avg=args.shift_avg, ref=args.ref)
        numpy.savetxt(args.output, results, delimiter='\t')

    # Estimate differential capacitance
    fit_2 = numpy.polyfit(results[:, 1], results[:, 2], 2)  # grand pot vs work function
    args.output.write(
        '\n\n'
        'Capacitance [e/V]\n'
        '{:.5f}\n'.format(-fit_2[0] * 2)
    )

    args.output.close()


if __name__ == '__main__':
    main()
