"""
Convert a XYZ file to a VASP geometry
"""

import argparse
import sys
import numpy

from ec_interface.molecular_geometry import MolecularGeometry
from ec_interface.scripts import get_lattice, get_vec


def get_arguments_parser():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('infile', help='source interface', type=argparse.FileType('r'))

    parser.add_argument('-l', '--lattice', help='lattice vector size', type=get_lattice, default='10,10,10')
    parser.add_argument('-s', '--shift', help='Shift positions', type=get_vec, default='0,0,0')
    parser.add_argument('--sort', help='sort atoms', action='store_true')

    parser.add_argument('-o', '--poscar', type=argparse.FileType('w'), default=sys.stdout)
    parser.add_argument('-C', '--cartesian', action='store_true', help='Output in cartesian coordinates')
    parser.add_argument('-S', '--selective', action='store_true', help='Use selective dynamics in output')

    return parser


def main():
    args = get_arguments_parser().parse_args()

    geometry = MolecularGeometry.from_xyz(args.infile)
    new_geometry = geometry.to_vasp(lattice_vectors=args.lattice, sort=args.sort, shift_positions=args.shift)

    if args.selective:
        new_geometry.selective_dynamics = numpy.ones((len(new_geometry), 3), dtype=bool)

    new_geometry.to_poscar(args.poscar, direct=not args.cartesian)


if __name__ == '__main__':
    main()
