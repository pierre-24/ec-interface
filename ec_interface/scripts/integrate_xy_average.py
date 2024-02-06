"""
Integrate XY-averaged charge data out of CHGCAR.
"""

import argparse

from ec_interface.vasp_results import VaspResultGrid


def get_arguments_parser():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('infile', help='source', type=argparse.FileType('r'))
    parser.add_argument('-t', '--threshold', default=1e-3, type=float)

    return parser


def main():
    args = get_arguments_parser().parse_args()

    print('! reading CHGCAR file')
    data = VaspResultGrid.from_file(args.infile)

    nZ = data.grid_data.shape[2]
    z_max = data.geometry.lattice_vectors[2, 2]
    xy_average = data.xy_average() / nZ

    total = xy_average.sum()
    print('Total = {:.3f} [e]'.format(total))

    regions = [0]

    print('! find regions of integration using threshold = {}'.format(args.threshold))
    # find areas
    for i in range(1, xy_average.shape[0]):
        if xy_average[i - 1] < args.threshold < xy_average[i] or xy_average[i - 1] > args.threshold > xy_average[i]:
            regions.append(i)

    regions.append(xy_average.shape[0])  # add last point to complete the integration over whole space

    print('Found {} regions'.format(len(regions) - 1))

    # sum
    print('! compute results')
    for i in range(1, len(regions)):
        beg, end = regions[i-1], regions[i]
        zbeg, zend = beg / nZ * z_max, end / nZ * z_max

        integ = xy_average[beg:end].sum()

        print('Charge in z ∈ [{:.3f},{:.3f}) = {:.3f} [e]'.format(
            zbeg,
            zend,
            integ
        ))


