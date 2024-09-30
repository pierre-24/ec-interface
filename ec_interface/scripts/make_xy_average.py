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
    parser.add_argument('-a', '--axis', default=2, type=int)
    parser.add_argument('-o', '--output', default=sys.stdout, type=argparse.FileType('w'))

    return parser


def main():
    args = get_arguments_parser().parse_args()

    data = VaspResultGrid.from_file(args.infile)

    N = data.grid_data.shape[args.axis]
    axis_max = data.geometry.lattice_vectors[args.axis, args.axis]
    values = numpy.arange(N) / N * axis_max
    planar_average = data.planar_average(args.axis)

    numpy.savetxt(
        args.output, numpy.array([values, planar_average.values, planar_average.values / N]).T, delimiter='\t')
