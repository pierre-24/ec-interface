"""
Get info about a slab geometry
"""

import argparse
import numpy

from ec_interface.vasp_geometry import Geometry


def get_arguments_parser():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('infile', help='source', type=argparse.FileType('r'))

    return parser


def main():
    args = get_arguments_parser().parse_args()

    geometry = Geometry.from_poscar(args.infile)

    if not numpy.allclose(geometry.lattice_vectors[2, :2], [.0, .0], rtol=1e-3):
        print('**WARNING: C lattice vector and Z axis does not match, this might affect the results!')

    print('Slab thickness: {:.4f} Å'.format(geometry.slab_thickness()))
    print('Slab surface: {:.4f} Å²'.format(numpy.linalg.det(geometry.lattice_vectors[:2, :2])))
    print('Interslab distance: {:.4f} Å'.format(geometry.interslab_distance()))
    print('Vacuum fraction: {:.4f}'.format(geometry.interslab_distance() / geometry.lattice_vectors[2, 2]))
