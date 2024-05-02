"""
Extract work function from a given calculation, for debugging purposes
"""

import argparse

from ec_interface.ec_results import _extract_data
from ec_interface.scripts import get_directory


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=get_directory, help='Directory where the calculation is')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose')

    args = parser.parse_args()

    # extract data
    _, _, fermi_energy, vacuum_potential, _ = _extract_data(args.directory, save_averages=False, verbose=args.verbose)
    print('{:.3f} [V]'.format(vacuum_potential - fermi_energy))


if __name__ == '__main__':
    main()
