import argparse
import sys

from ec_interface.vasp_geometry import Geometry


def get_arguments_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('infile', help='source', type=argparse.FileType('r'))
    parser.add_argument('-v', '--vacuum', type=float, default=5.0)

    parser.add_argument('-o', '--poscar', type=argparse.FileType('w'), default=sys.stdout)

    return parser


def main():
    args = get_arguments_parser().parse_args()

    geometry = Geometry.from_poscar(args.infile)
    new_geometry = geometry.change_interslab_distance(args.vacuum)

    args.poscar.write(str(new_geometry))


if __name__ == '__main__':
    main()
