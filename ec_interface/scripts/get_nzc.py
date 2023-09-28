"""
Get the value of NELECT for zero-charge system
"""

import argparse

from ec_interface.vasp_geometry import Geometry


def get_arguments_parser():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('infile', help='source', type=argparse.FileType('r'))
    parser.add_argument('-p', '--potcar', help='POTCAR file', type=argparse.FileType('r'), required=True)

    return parser


def main():
    args = get_arguments_parser().parse_args()

    # get geometry
    geometry = Geometry.from_poscar(args.infile)
    print(geometry.nelect(args.potcar))
