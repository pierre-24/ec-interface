import numpy
import pathlib
import h5py

from typing import Tuple
from numpy.typing import NDArray

from ec_interface.vasp_results import VaspResultsH5, VaspChgCar, VaspLocPot
from ec_interface.ec_parameters import ECParameters


def assert_exists(p: pathlib.Path):
    if not p.exists():
        raise FileNotFoundError('file `{}` does not exists'.format(p))

    return p


def _extract_data(
    directory: pathlib.Path, save_averages: bool = True, verbose: bool = True
) -> Tuple[float, float, float, float, float]:
    """Extract the data (`nelect, free_energy, fermi_energy, reference_potential`) from a calculation.
     Results are obtained from `vaspout.h5`, `CHGCAR` and `LOCPOT`.
    """

    def _outverb(*args_, **kwargs):
        if verbose:
            print(*args_, **kwargs)

    # get free energy, number of electron and fermi energy from vaspout.h5
    path_h5 = assert_exists(directory / 'vaspout.h5')
    _outverb('  - Reading', path_h5, end='... ', flush=True)
    data_h5 = VaspResultsH5.from_h5(path_h5)
    _outverb('OK')

    _outverb('  → NELECT = {:.3f} [e]'.format(data_h5.nelect))
    _outverb('  → Fermi energy = {:.3f} [V]'.format(data_h5.fermi_energy))

    # find the vaccum zone in CHGCAR
    path_chgcar = assert_exists(directory / 'CHGCAR')
    _outverb('  - Reading', path_chgcar, end='... ', flush=True)
    with path_chgcar.open() as f:
        data_charge_density = VaspChgCar.from_file(f)
    _outverb('OK')

    # determine where the charge density is the closest to zero
    nZ = data_charge_density.grid_data.shape[2]
    z_max = data_charge_density.geometry.lattice_vectors[2, 2]
    z_inc = z_max / nZ

    xy_average_charge_density = data_charge_density.xy_planar_average()
    z_min_charge_density_index = xy_average_charge_density.argmin()
    z_charge_density_value = xy_average_charge_density[z_min_charge_density_index]

    _outverb('  → Charge density is minimal at z = {:.3f} (n.V = {:.3e} [e Å³])'.format(
        z_min_charge_density_index * z_inc, z_charge_density_value))

    # determine a vacuum area, and a vacuum center
    z_vacuum_min_index, z_vacuum_center_index, z_vacuum_max_index = xy_average_charge_density.get_vacuum()

    _outverb('  → Selected vacuum area: z ∈ [{:.3f},{:.3f})'.format(
        z_vacuum_min_index * z_inc, z_vacuum_max_index * z_inc))

    # determine reference potential as the value of the local potential at the vacuum center
    path_locpot = assert_exists(directory / 'LOCPOT')
    _outverb('  - Reading', path_locpot, end='... ', flush=True)
    with path_locpot.open() as f:
        data_local_potential = VaspLocPot.from_file(f)
    _outverb('OK')

    xy_average_local_potential = data_local_potential.xy_planar_average()
    vacuum_potential = xy_average_local_potential[z_vacuum_center_index]
    _outverb('  → Vacuum potential (z={:.3f}) = {:.3f} [eV]'.format(
        z_vacuum_center_index * z_inc, vacuum_potential))

    average_potential = xy_average_local_potential.sum() / nZ
    _outverb('  → Average potential in cell = {:.3f} [eV]'.format(average_potential))

    _outverb('  → Corresponding work function = {:.3f} [V]'.format(vacuum_potential - data_h5.fermi_energy))

    if save_averages:
        # save chg & locpot
        _outverb('  - Writing xy-averaged charge and potential', end='... ', flush=True)

        z_values = numpy.arange(nZ) / nZ * z_max
        with (directory / 'charge_density_xy_avg.csv').open('w') as f:
            f.write('\n'.join(
                '{:.5f}\t{:.5e}\t{:.5e}\t{:.5e}'.format(z, chg, chg / nZ, chgs / nZ)
                for z, chg, chgs in
                zip(z_values, xy_average_charge_density.values, numpy.cumsum(xy_average_charge_density.values))
            ))

        with (directory / 'local_potential_xy_avg.csv').open('w') as f:
            f.write('\n'.join(
                '{:.5f}\t{:.5f}'.format(z, chg) for z, chg in zip(z_values, xy_average_local_potential.values)
            ))

        _outverb('OK')

    # return data
    return data_h5.nelect, data_h5.free_energy, data_h5.fermi_energy, vacuum_potential, average_potential


def _extract_data_from_directories(
    ec_parameters: ECParameters, directory: pathlib.Path, verbose: bool = False
) -> NDArray:
    """Extract data from the directories where calculations were performed.
    """

    def _outverb(*args_, **kwargs):
        if verbose:
            print(*args_, **kwargs)

    _outverb('extracting data from', str(ec_parameters))
    _outverb('-' * 50)

    nelects = []
    free_energies = []
    fermi_energies = []
    vacuum_potentials = []
    average_potetials = []

    n = 0
    for subdirectory in ec_parameters.directories(directory):
        _outverb('*', subdirectory, '...')

        try:
            if not subdirectory.exists():
                raise FileNotFoundError('directory `{}` does not exists'.format(subdirectory))

            nelect, free_energy, fermi_energy, vacuum_potential, average_potential \
                = _extract_data(subdirectory, verbose=verbose)

            nelects.append(nelect)
            free_energies.append(free_energy)
            fermi_energies.append(fermi_energy)
            vacuum_potentials.append(vacuum_potential)
            average_potetials.append(average_potential)

            n += 1

        except Exception as e:
            print('error in {}:'.format(subdirectory), e, '→ skipped')

    _outverb('-' * 50)

    dataset = numpy.array([nelects, free_energies, fermi_energies, vacuum_potentials, average_potetials]).T
    return dataset


class ECResults:
    def __init__(
        self,
        ne_zc: float,
        data: NDArray
    ):
        assert data.shape[1] == 5
        self.ne_zc = ne_zc

        # gather data from directories
        self.data = data
        self.nelects = data[:, 0]
        self.free_energies = data[:, 1]
        self.fermi_energies = data[:, 2]
        self.vacuum_potentials = data[:, 3]
        self.average_potentials = data[:, 4]

    @classmethod
    def from_calculations(cls, ec_parameters: ECParameters, directory: pathlib.Path, verbose: bool = False):
        return cls(ec_parameters.ne_zc, _extract_data_from_directories(ec_parameters, directory, verbose))

    def __len__(self):
        return self.nelects.shape[0]

    def to_hdf5(self, path: pathlib.Path):
        """Save data in a HDF5 file"""

        with h5py.File(path, 'w') as f:
            dset = f.create_dataset('ec_results', data=self.data)
            dset.attrs['version'] = 1

    @classmethod
    def from_hdf5(cls, ne_zc: float, path: pathlib.Path):
        with h5py.File(path) as f:
            if 'ec_results' not in f:
                raise Exception('invalid h5 file: no `ec_results` dataset')

            dset = f['ec_results']
            if 'version' not in dset.attrs or dset.attrs['version'] > 1:
                raise Exception('unknown version for dataset, use a more recent version of this package!')

            return cls(ne_zc, dset[:])

    def estimate_active_fraction(self, shift_with_avg: bool = False) -> float:
        """Estimate the active fraction from estimates of the surface capacitance.
        """

        work_function = self.vacuum_potentials - self.fermi_energies
        dnelect = self.nelects - self.ne_zc

        shift_fee = .0
        if shift_with_avg:
            index_0 = numpy.where(dnelect == .0)[0][0]
            shift_fee = self.average_potentials[index_0]

        fee = self.free_energies - dnelect * self.fermi_energies - shift_fee

        fit_1 = numpy.polyfit(work_function, dnelect, 1)  # charge vs work function
        cap_1 = -fit_1[0]
        fit_2 = numpy.polyfit(work_function, fee, 2)  # grand pot vs work function
        cap_2 = -fit_2[0] * 2

        return cap_2 / cap_1

    def compute_fee_hbm(self, alpha: float, shift_with_avg: bool = False, ref: float = 4.5):
        """Compute the Free electrochemical energy (grand potential) assuming a homogeneous background method
        calculation. `alpha` is the vacuum fraction.
        """

        work_function = self.vacuum_potentials - self.fermi_energies
        dnelect = self.nelects - self.ne_zc

        # find 0 and corresponding energy
        index_0 = numpy.where(dnelect == .0)[0][0]
        fe0 = self.free_energies[index_0]

        shift_fee = .0
        if shift_with_avg:
            index_0 = numpy.where(dnelect == .0)[0][0]
            shift_fee = self.average_potentials[index_0]

        # integrate vacuum potential
        integ_average_pot = []
        for i in range(len(self.vacuum_potentials)):
            b0, b1 = i if i < index_0 else index_0, (index_0 if i < index_0 else i) + 1
            integ_average_pot.append((-1 if i < index_0 else 1) * numpy.trapz(
                self.vacuum_potentials[b0:b1],
                dnelect[b0:b1]
            ))

        fee = fe0 + alpha * (self.free_energies - fe0 + dnelect * work_function - integ_average_pot)

        # get fee:
        return numpy.array([dnelect, work_function, work_function - ref, fee - shift_fee]).T

    def compute_fee_hbm_fermi(self, shift_with_avg: bool = False, ref: float = 4.5):
        """Compute the Free electrochemical energy (grand potential) assuming a homogeneous background method
        calculation, and use the Fermi energy as the work function.
        """

        work_function = self.vacuum_potentials - self.fermi_energies
        dnelect = self.nelects - self.ne_zc
        fee = self.free_energies - dnelect * self.fermi_energies

        shift_fee = .0
        if shift_with_avg:
            index_0 = numpy.where(dnelect == .0)[0][0]
            shift_fee = self.average_potentials[index_0]

        return numpy.array([dnelect, work_function, work_function - ref, fee - shift_fee]).T

    def compute_fee_pbm(self, shift_with_avg: bool = False, ref: float = 4.5) -> NDArray:
        """Compute the Free electrochemical energy (grand potential) assuming a Poisson-Boltzmann method
        calculation"""

        work_function = self.vacuum_potentials - self.fermi_energies
        dnelect = self.nelects - self.ne_zc
        fee = self.free_energies + dnelect * work_function

        shift_fee = .0
        if shift_with_avg:
            index_0 = numpy.where(dnelect == .0)[0][0]
            shift_fee = self.average_potentials[index_0]

        return numpy.array([dnelect, work_function, work_function - ref, fee - shift_fee]).T
