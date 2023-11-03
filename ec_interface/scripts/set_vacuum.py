"""
Change the interslab distance
"""

import argparse
import sys

import numpy

from ec_interface.vasp_geometry import Geometry


def get_arguments_parser():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('infile', help='source', type=argparse.FileType('r'))
    parser.add_argument('-v', '--vacuum', type=float, default=5.0)

    parser.add_argument('-o', '--poscar', type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('-C', '--cartesian', action='store_true', help='Output in cartesian coordinates')
    parser.add_argument('-S', '--selective', action='store_true', help='Use selective dynamics')

    return parser


def main():
    args = get_arguments_parser().parse_args()

    geometry = Geometry.from_poscar(args.infile)
    new_geometry = geometry.change_interslab_distance(args.vacuum)

    if args.selective:
        new_geometry.selective_dynamics = numpy.ones((len(new_geometry), 3), dtype=bool)

    new_geometry.to_poscar(args.poscar, direct=not args.cartesian)


if __name__ == '__main__':
    main()
