"""
Merge two POSCAR geometries into a single.
The lattice vector of the first geometry is used in the final one.
"""

import argparse
import sys

from ec_interface.scripts import get_vec
from ec_interface.vasp_geometry import Geometry


def get_arguments_parser():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('infile', help='source', type=argparse.FileType('r'))
    parser.add_argument('additional', help='additional', type=argparse.FileType('r'))

    parser.add_argument('-s', '--shift', help='Shift positions', type=get_vec, default='0,0,0')

    parser.add_argument('-o', '--poscar', type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('-C', '--cartesian', action='store_true', help='Output in cartesian coordinates')

    return parser


def main():
    args = get_arguments_parser().parse_args()

    geometry = Geometry.from_poscar(args.infile)
    additional = Geometry.from_poscar(args.additional)
    geometry.merge_with(additional, shift=args.shift).to_poscar(args.poscar, direct=not args.cartesian)


if __name__ == '__main__':
    main()
