"""
Make XY-averaged data out of CHGCAR, LOCPOT, or other files with similar layouts.
"""

import argparse
import sys
import numpy

from ec_interface.vasp_results import VaspResultGrid


def get_arguments_parser():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('infile', help='source', type=argparse.FileType('r'))
    parser.add_argument('-o', '--output', default=sys.stdout, type=argparse.FileType('w'))

    return parser


def main():
    args = get_arguments_parser().parse_args()

    data = VaspResultGrid.from_file(args.infile)

    nZ = data.grid_data.shape[2]
    z_max = data.geometry.lattice_vectors[2, 2]
    z_values = numpy.arange(nZ) / nZ * z_max
    xy_average = data.xy_average()

    numpy.savetxt(args.output, numpy.array([z_values, xy_average, xy_average / nZ]).T, delimiter='\t')
