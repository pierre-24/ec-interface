"""
Integrate density (CHGCAR) along an axis (by default, Z) and integrate in regions.
"""

import argparse

from ec_interface.vasp_results import VaspResultGrid


def get_arguments_parser():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('infile', help='source', type=argparse.FileType('r'))
    parser.add_argument('-a', '--axis', default=2, type=int)
    parser.add_argument('-t', '--threshold', default=1e-3, type=float)

    return parser


def main():
    args = get_arguments_parser().parse_args()

    print('! reading CHGCAR file')
    data = VaspResultGrid.from_file(args.infile)

    N = data.grid_data.shape[args.axis]
    axis_max = data.geometry.lattice_vectors[args.axis, args.axis]
    density = data.planar_average(args.axis).values / N

    total = density.sum()
    print('Total = {:.3f} [e]'.format(total))

    regions = [0]

    print('! find regions of integration using threshold = {}'.format(args.threshold))
    # find areas
    for i in range(1, density.shape[0]):
        if density[i - 1] < args.threshold < density[i] or density[i - 1] > args.threshold > density[i]:
            regions.append(i)

    regions.append(density.shape[0])  # add last point to complete the integration over whole space

    print('Found {} regions'.format(len(regions) - 1))

    # sum
    print('! compute results')
    for i in range(1, len(regions)):
        beg, end = regions[i - 1], regions[i]
        zbeg, zend = beg / N * axis_max, end / N * axis_max

        integ = density[beg:end].sum()

        print('Charge in z ∈ [{:.3f},{:.3f}) = {:.3f} [e]'.format(
            zbeg,
            zend,
            integ
        ))
