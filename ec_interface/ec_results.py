import numpy
import pathlib

from typing import Tuple, Optional
from numpy.typing import NDArray

from ec_interface.vasp_results import VaspResultsH5, VaspChgCar, VaspLocPot
from ec_interface.ec_parameters import ECParameters


def assert_exists(p: pathlib.Path):
    if not p.exists():
        raise FileNotFoundError('file `{}` does not exists'.format(p))

    return p


class ECResults:
    def __init__(self, ec_parameters: ECParameters, directory: pathlib.Path, verbose: bool = False):
        self.ec_parameters = ec_parameters
        self.verbose = verbose

        # gather data from directories
        self.nelects: Optional[NDArray] = None
        self.free_energies: Optional[NDArray] = None
        self.fermi_energies: Optional[NDArray] = None
        self.vacuum_potentials: Optional[NDArray] = None
        self.average_potentials: Optional[NDArray] = None

        self._extract_data_from_directories(directory)

    def __len__(self):
        return self.nelects.shape[0]

    def _outverb(self, *args, **kwargs):
        if self.verbose:
            print(*args, **kwargs)

    def _extract_data(
            self, directory: pathlib.Path, save_averages: bool = True
    ) -> Tuple[float, float, float, float, float]:
        """Extract the data (`nelect, free_energy, fermi_energy, reference_potential`) from a calculation.
         Results are obtained from `vaspout.h5`, `CHGCAR` and `LOCPOT`.
        """

        # get free energy, number of electron and fermi energy from vaspout.h5
        path_h5 = assert_exists(directory / 'vaspout.h5')
        self._outverb('  - Reading', path_h5, end='... ', flush=True)
        data_h5 = VaspResultsH5.from_h5(path_h5)
        self._outverb('OK')

        self._outverb('  → NELECT = {:.3f} [e]'.format(data_h5.nelect))
        self._outverb('  → Fermi energy = {:.3f} [V]'.format(data_h5.fermi_energy))

        # find the vaccum zone in CHGCAR
        path_chgcar = assert_exists(directory / 'CHGCAR')
        self._outverb('  - Reading', path_chgcar, end='... ', flush=True)
        with path_chgcar.open() as f:
            data_charge_density = VaspChgCar.from_file(f)
        self._outverb('OK')

        # determine where the charge density is the closest to zero
        nZ = data_charge_density.grid_data.shape[2]
        z_max = data_charge_density.geometry.lattice_vectors[2, 2]
        z_inc = z_max / nZ

        xy_average_charge_density = data_charge_density.xy_average()
        z_min_charge_density_index = numpy.argmin(xy_average_charge_density)
        z_charge_density_value = xy_average_charge_density[z_min_charge_density_index]

        self._outverb('  → Charge density is minimal at z = {:.3f} (n.V = {:.3e} [e Å³])'.format(
            z_min_charge_density_index * z_inc, z_charge_density_value))

        # determine a vacuum area, and a vacuum center
        z_vacuum_max_index = z_vacuum_min_index = z_min_charge_density_index

        while numpy.abs(
                xy_average_charge_density[
                    z_vacuum_max_index - int(z_vacuum_max_index / nZ) * nZ] - z_charge_density_value
        ) < 1e-3:
            z_vacuum_max_index += 1

        while numpy.abs(xy_average_charge_density[z_vacuum_min_index] - z_charge_density_value) < 1e-3:
            z_vacuum_min_index -= 1

        z_vacuum_center_index = int((z_vacuum_min_index + z_vacuum_max_index) / 2)
        if z_vacuum_center_index < 0:
            z_vacuum_center_index += nZ
        elif z_vacuum_center_index >= nZ:
            z_vacuum_center_index -= nZ

        self._outverb('  → Selected vacuum area: z = [{:.3f}, {:.3f}]'.format(
            z_vacuum_min_index * z_inc, z_vacuum_max_index * z_inc))

        # determine reference potential as the value of the local potential at the vacuum center
        path_locpot = assert_exists(directory / 'LOCPOT')
        self._outverb('  - Reading', path_locpot, end='... ', flush=True)
        with path_locpot.open() as f:
            data_local_potential = VaspLocPot.from_file(f)
        self._outverb('OK')

        xy_average_local_potential = data_local_potential.xy_average()
        vacuum_potential = xy_average_local_potential[z_vacuum_center_index]
        self._outverb('  → Vacuum potential (z={:.3f}) = {:.3f} [eV]'.format(
            z_vacuum_center_index * z_inc, vacuum_potential))

        average_potential = numpy.sum(xy_average_local_potential) / nZ
        self._outverb('  → Average potential in cell = {:.3f} [eV]'.format(average_potential))

        self._outverb('  → Corresponding work function = {:.3f} [V]'.format(vacuum_potential - data_h5.fermi_energy))

        if save_averages:
            # save chg & locpot
            self._outverb('  - Writing xy-averaged charge and potential', end='... ', flush=True)

            z_values = numpy.arange(nZ) / nZ * z_max
            with (directory / 'charge_density_xy_avg.csv').open('w') as f:
                f.write('\n'.join(
                    '{:.5f}\t{:.5e}\t{:.5e}\t{:.5e}'.format(z, chg, chg / nZ, chgs / nZ)
                    for z, chg, chgs in
                    zip(z_values, xy_average_charge_density, numpy.cumsum(xy_average_charge_density))
                ))

            with (directory / 'local_potential_xy_avg.csv').open('w') as f:
                f.write('\n'.join(
                    '{:.5f}\t{:.5f}'.format(z, chg) for z, chg in zip(z_values, xy_average_local_potential)
                ))

            self._outverb('OK')

        # return data
        return data_h5.nelect, data_h5.free_energy, data_h5.fermi_energy, vacuum_potential, average_potential

    def _extract_data_from_directories(self, directory: pathlib.Path):
        """Extract data from the directories where calculations were performed.
        """

        self._outverb('extracting data from', str(self.ec_parameters))
        self._outverb('-' * 50)

        nelects = []
        free_energies = []
        fermi_energies = []
        vacuum_potentials = []
        average_potetials = []

        for subdirectory in self.ec_parameters.directories(directory):
            self._outverb('*', subdirectory, '...')

            try:
                if not subdirectory.exists():
                    raise FileNotFoundError('directory `{}` does not exists'.format(subdirectory))

                nelect, free_energy, fermi_energy, vacuum_potential, average_potential \
                    = self._extract_data(subdirectory)

                nelects.append(nelect)
                free_energies.append(free_energy)
                fermi_energies.append(fermi_energy)
                vacuum_potentials.append(vacuum_potential)
                average_potetials.append(average_potential)

            except Exception as e:
                print('error in {}:'.format(subdirectory), e, '→ skipped')

        self._outverb('-' * 50)

        self.nelects = numpy.array(nelects)
        self.free_energies = numpy.array(free_energies)
        self.fermi_energies = numpy.array(fermi_energies)
        self.vacuum_potentials = numpy.array(vacuum_potentials)
        self.average_potentials = numpy.array(average_potetials)

    def estimate_active_fraction(self) -> float:
        """Estimate the active fraction from estimates of the surface capacitance.
        """

        work_function = self.vacuum_potentials - self.fermi_energies
        dnelect = self.nelects - self.ec_parameters.ne_zc
        fee = self.free_energies - dnelect * self.fermi_energies

        fit_1 = numpy.polyfit(work_function, dnelect, 1)  # charge vs work function
        cap_1 = -fit_1[0]
        fit_2 = numpy.polyfit(work_function, fee, 2)  # grand pot vs work function
        cap_2 = -fit_2[0] * 2

        self._outverb('Capacitance [e/V] = {:.5f} (charge), {:.5f} (grand potential), active fraction: {:.3f}'.format(
            cap_1, cap_2, cap_2 / cap_1
        ))

        return cap_2 / cap_1

    def compute_fee_hbm(self, alpha: float):
        """Compute the Free electrochemical energy (grand potential) assuming a homogeneous background method
        calculation. `alpha` is the vacuum fraction.
        """

        pass

    def compute_fee_pbm(self) -> NDArray:
        """Compute the Free electrochemical energy (grand potential) assuming a Poisson-Boltzmann method
        calculation"""

        work_function = self.vacuum_potentials - self.fermi_energies
        dnelect = self.nelects - self.ec_parameters.ne_zc
        fee = self.free_energies - dnelect * work_function

        return numpy.hstack(work_function, fee)
