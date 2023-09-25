"""
Extract data form calculations
"""

import argparse
import pathlib
import sys

import numpy

from ec_interface.ec_parameters import ECParameters
from ec_interface.vasp_results import VaspResultsH5, VaspChgCar, VaspLocPot
from ec_interface.scripts import get_directory, INPUT_NAME, assert_exists


def extract_data_from_directory(directory: pathlib.Path, save_averages: bool = True):
    """Extract the data from a calculation.
     Results are obtained from `vaspout.h5`, `CHGCAR` and `LOCPOT`.
    """

    # get free energy, number of electron and fermi energy from vaspout.h5
    path_h5 = assert_exists(directory / 'vaspout.h5')
    data_h5 = VaspResultsH5.from_h5(path_h5)

    # find the vaccum zone in CHGCAR
    path_chgcar = assert_exists(directory / 'CHGCAR')
    with path_chgcar.open() as f:
        data_charge_density = VaspChgCar.from_file(f)

    # determine where the charge density is the closest to zero
    nZ = data_charge_density.grid_data.shape[2]
    z_max = data_charge_density.geometry.lattice_vectors[2, 2]
    xy_average_charge_density = data_charge_density.xy_average()
    z_min_charge_density_index = numpy.argmin(numpy.abs(xy_average_charge_density))
    z_min_charge_density = z_min_charge_density_index / nZ * z_max

    # determine a vacuum area, and a vacuum center
    z_coordinates = data_charge_density.geometry.cartesian_coordinates()[:, 2]
    z_vacuum_max = numpy.min(z_coordinates)
    z_vacuum_min = numpy.max(z_coordinates)

    if z_min_charge_density < z_vacuum_max:
        z_vacuum_max, z_vacuum_min = z_vacuum_min - z_max, z_vacuum_max
    else:
        z_vacuum_max, z_vacuum_min = z_vacuum_min, z_vacuum_max + z_max

    z_vacuum_center = (z_vacuum_min + z_vacuum_max) / 2
    if z_vacuum_center < 0:
        z_vacuum_center += z_max
    if z_vacuum_center >= z_max:
        z_vacuum_center -= z_max

    z_vacuum_center_index = int(z_vacuum_center / z_max * nZ)

    # determine reference potential as the value of the local potential at the vacuum center
    path_locpot = assert_exists(directory / 'LOCPOT')
    with path_locpot.open() as f:
        data_local_potential = VaspLocPot.from_file(f)

    xy_average_local_potential = data_local_potential.xy_average()
    reference_potential = xy_average_local_potential[z_vacuum_center_index]

    if save_averages:
        # save chg & locpot
        z_values = numpy.arange(nZ) / nZ * z_max
        with (directory / 'charge_density_xy_avg.csv').open('w') as f:

            f.write('\n'.join(
                '{:.5f}\t{:.5e}\t{:.5e}\t{:.5e}'.format(z, chg, chg / nZ, chgs / nZ)
                for z, chg, chgs in zip(z_values, xy_average_charge_density, numpy.cumsum(xy_average_charge_density))
            ))

        with (directory / 'local_potential_xy_avg.csv').open('w') as f:
            f.write('\n'.join(
                '{:.5f}\t{:.5f}'.format(z, chg) for z, chg in zip(z_values, xy_average_local_potential)
            ))

    # return data
    return data_h5.nelect, data_h5.free_energy, data_h5.fermi_energy, reference_potential


def extract_data_from_directories(directory: pathlib.Path, verbose: bool = False):
    """Extract data from the directories where calculations were performed.
    """

    ec_input_file = directory / INPUT_NAME
    if not ec_input_file.exists():
        raise FileNotFoundError('file `{}` does not exists'.format(ec_input_file))

    with ec_input_file.open() as f:
        ec_parameters = ECParameters.from_yaml(f)

    if verbose:
        print('extracting data from', str(ec_parameters))

    data = []

    for subdirectory in ec_parameters.directories(directory):
        if verbose:
            print(subdirectory, '...', end=' ', flush=True)

        if not subdirectory.exists():
            raise FileNotFoundError('directory `{}` does not exists'.format(subdirectory))

        nelect, free_energy, fermi_energy, ref_potential = extract_data_from_directory(subdirectory)
        dnelect = nelect - ec_parameters.ne_zc
        work_function = ref_potential - fermi_energy
        grand_potential = free_energy - dnelect * fermi_energy

        data_pot = [dnelect, free_energy, fermi_energy, ref_potential, work_function, grand_potential]
        data.append(data_pot)

        if verbose:
            print('ok', flush=True)

    # create and save dataframe
    data_frame = numpy.array(data)

    with (directory / 'ec_result.csv').open('w') as f:
        f.write(
            'Charge\t'
            'Free energy [eV]\t'
            'Fermi energy [eV]\t'
            'Ref. potential [eV]\t'
            'Work function [V]\t'
            'Grand potential [V]\n'
        )

        numpy.savetxt(f, data_frame, delimiter='\t')

    # if verbose, compute the capacitance
    if verbose:
        fit_1 = numpy.polyfit(data_frame[:, 4], data_frame[:, 0], 1)
        cap_1 = -fit_1[0]
        fit_2 = numpy.polyfit(data_frame[:, 4], data_frame[:, 5], 2)
        cap_2 = -fit_2[0] * 2

        print('Capacitance [e/V] = {:.5f} (charge), {:.5f} (grand potential), Vacuum fraction: {:.3f}'.format(
            cap_1, cap_2, cap_2 / cap_1
        ))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('-i', '--directory', default='.', type=get_directory, help='Input directory')
    parser.add_argument('-v', '--verbose', action='store_true', help='Verbose')
    args = parser.parse_args()

    # extract data
    try:
        extract_data_from_directories(args.directory, verbose=args.verbose)
    except Exception as e:
        print('error:', e, file=sys.stderr)


if __name__ == '__main__':
    main()
