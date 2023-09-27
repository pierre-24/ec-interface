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


def extract_data_from_directory(directory: pathlib.Path, save_averages: bool = True, verbose: bool = False):
    """Extract the data (`nelect, free_energy, fermi_energy, reference_potential`) from a calculation.
     Results are obtained from `vaspout.h5`, `CHGCAR` and `LOCPOT`.
    """

    def _outverb(*args, **kwargs):
        if verbose:
            print(*args, **kwargs)

    # get free energy, number of electron and fermi energy from vaspout.h5
    path_h5 = assert_exists(directory / 'vaspout.h5')
    _outverb('  - Reading', path_h5, end='... ', flush=True)
    data_h5 = VaspResultsH5.from_h5(path_h5)
    _outverb('Ok')

    # find the vaccum zone in CHGCAR
    path_chgcar = assert_exists(directory / 'CHGCAR')
    _outverb('  - Reading', path_chgcar, end='... ', flush=True)
    with path_chgcar.open() as f:
        data_charge_density = VaspChgCar.from_file(f)
    _outverb('Ok')

    # determine where the charge density is the closest to zero
    nZ = data_charge_density.grid_data.shape[2]
    z_max = data_charge_density.geometry.lattice_vectors[2, 2]
    z_inc = z_max / nZ

    xy_average_charge_density = data_charge_density.xy_average()
    z_min_charge_density_index = numpy.argmin(numpy.abs(xy_average_charge_density))

    _outverb('  → Charge density is minimal at z = {:.3f} (n = {:.3e} [e Å³])'.format(
        z_min_charge_density_index * z_inc, xy_average_charge_density[z_min_charge_density_index]))

    # determine a vacuum area, and a vacuum center
    z_vacuum_max_index = z_vacuum_min_index = z_min_charge_density_index

    while xy_average_charge_density[z_vacuum_max_index - int(z_vacuum_max_index / nZ) * nZ] < 1e-3:
        z_vacuum_max_index += 1

    while xy_average_charge_density[z_vacuum_min_index] < 1e-3:
        z_vacuum_min_index -= 1

    z_vacuum_center_index = int((z_vacuum_min_index + z_vacuum_max_index) / 2)
    if z_vacuum_center_index < 0:
        z_vacuum_center_index += nZ
    elif z_vacuum_center_index >= nZ:
        z_vacuum_center_index -= nZ

    _outverb('  → Selected vacuum area: z = [{:.3f}, {:.3f}]'.format(
        z_vacuum_min_index * z_inc, z_vacuum_max_index * z_inc))

    # determine reference potential as the value of the local potential at the vacuum center
    path_locpot = assert_exists(directory / 'LOCPOT')
    _outverb('  - Reading', path_locpot, end='... ', flush=True)
    with path_locpot.open() as f:
        data_local_potential = VaspLocPot.from_file(f)
    _outverb('Ok')

    xy_average_local_potential = data_local_potential.xy_average()
    reference_potential = xy_average_local_potential[z_vacuum_center_index]
    _outverb('  → Reference potential (z={:.3f}) = {:.3f} [eV]'.format(
        z_vacuum_center_index * z_inc, reference_potential))

    if save_averages:
        # save chg & locpot
        _outverb('  - Writing xy-average charge and potential', end='... ', flush=True)

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

        _outverb('Ok')

    # return data
    return data_h5.nelect, data_h5.free_energy, data_h5.fermi_energy, reference_potential


def extract_data_from_directories(directory: pathlib.Path, verbose: bool = False):
    """Extract data from the directories where calculations were performed.
    """

    def _outverb(*args, **kwargs):
        if verbose:
            print(*args, **kwargs)

    ec_input_file = directory / INPUT_NAME
    if not ec_input_file.exists():
        raise FileNotFoundError('file `{}` does not exists'.format(ec_input_file))

    with ec_input_file.open() as f:
        ec_parameters = ECParameters.from_yaml(f)

    _outverb('extracting data from', str(ec_parameters))
    _outverb('-' * 50)

    data = []

    for subdirectory in ec_parameters.directories(directory):
        _outverb('*', subdirectory, '...')

        if not subdirectory.exists():
            raise FileNotFoundError('directory `{}` does not exists'.format(subdirectory))

        nelect, free_energy, fermi_energy, ref_potential = extract_data_from_directory(subdirectory, verbose=verbose)
        dnelect = nelect - ec_parameters.ne_zc
        work_function = ref_potential - fermi_energy
        grand_potential = free_energy - dnelect * fermi_energy

        data_pot = [dnelect, free_energy, fermi_energy, ref_potential, work_function, grand_potential]
        data.append(data_pot)

    _outverb('-' * 50)

    # create and save dataframe
    data_frame = numpy.array(data)

    _outverb('Writing `ec_result.csv`', end='... ', flush=True)

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

    _outverb('Ok')

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
