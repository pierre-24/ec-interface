"""
Create a POTCAR file
"""

import argparse
import pathlib

from ec_interface.vasp_geometry import Geometry
from typing import Dict


def translate_list(inp: str) -> Dict[str, str]:
    tr = {}
    if len(inp) > 0:
        chunks = inp.split(',')
        for chunk in chunks:
            try:
                key, val = chunk.split('=')
                tr[key] = val
            except ValueError:
                raise argparse.ArgumentTypeError('Must be `key=val`')

    return tr


def to_directory(inp: str) -> pathlib.Path:
    path = pathlib.Path(inp)
    if not path.is_dir():
        raise argparse.ArgumentTypeError('`{}` is not a directory'.format(inp))

    return path


def get_arguments_parser():
    parser = argparse.ArgumentParser(description=__doc__)

    parser.add_argument('infile', help='source', type=argparse.FileType('r'))
    parser.add_argument('-p', '--potpaw', type=to_directory, help='Root of VASP PP', required=True)
    parser.add_argument(
        '-P', '--pseudos', type=translate_list, help='replace a given symbol by a different PP', default=''
    )
    parser.add_argument('-o', '--output', help='output', type=argparse.FileType('w'), default='POTCAR')

    return parser


def main():
    args = get_arguments_parser().parse_args()

    # get geometry
    geometry = Geometry.from_poscar(args.infile)

    # make POTCAR
    for ion_type in geometry.ion_types:
        try:
            ion_type = args.pseudos[ion_type]
        except KeyError:
            pass

        potcar_ion_path = args.potpaw / ion_type / 'POTCAR'
        with potcar_ion_path.open() as f:
            args.output.write(f.read())
