"""
Compute the Fukui function
"""

import argparse
import sys

from ec_interface.vasp_results import VaspResultGrid


def get_arguments_parser():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('ref', help='ρ(N) (CHGCAR)', type=argparse.FileType('r'))
    parser.add_argument('add', help='ρ(N+ΔN) (CHGCAR)', type=argparse.FileType('r'))
    parser.add_argument(
        '-s', '--symmetric', help='ref is ρ(N-ΔN) instead and symmetric difference is used', action='store_true')
    parser.add_argument('-d', '--delta', help='value of Δe', type=float, required=True)

    parser.add_argument('-o', '--output', default=sys.stdout, type=argparse.FileType('w'))

    return parser


def main():
    args = get_arguments_parser().parse_args()

    # read up
    print('! reading {} CHGCAR file'.format('ρ(N-ΔN)' if args.symmetric else 'ρ(N)'))
    data_ref = VaspResultGrid.from_file(args.ref)
    print('! reading ρ(N+ΔN) CHGCAR file')
    data_add = VaspResultGrid.from_file(args.add)

    # differentiate
    print('! differentiate{}'.format(' using symmetric difference' if args.symmetric else ''))
    new_data = VaspResultGrid(
        data_ref.geometry,
        (data_add.grid_data - data_ref.grid_data) / ((2 if args.symmetric else 1) * args.delta)
    )

    # save
    print('! write result')
    new_data.to_file(args.output)
