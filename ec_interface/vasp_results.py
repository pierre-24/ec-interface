import pathlib
import h5py
import numpy

from numpy.typing import NDArray
from typing import TextIO

from ec_interface.vasp_geometry import Geometry


class VaspResultsH5:
    def __init__(self, nelect: float, free_energy: float, fermi_energy: float):
        self.nelect = nelect
        self.free_energy = free_energy
        self.fermi_energy = fermi_energy

    @classmethod
    def from_h5(cls, path: pathlib.Path):
        with h5py.File(path, 'r') as f:
            nelect = f['results/electron_eigenvalues/nelectrons'][()]
            free_energy = f['intermediate/ion_dynamics/energies'][0][2]  # energy(sigma -> 0)
            fermi_energy = f['results/electron_dos/efermi'][()]

        return cls(nelect, free_energy, fermi_energy)


class PlanarAverage:
    """Stores a  planar average"""

    def __init__(self, values: NDArray):
        self.values = values

    def sum(self) -> float:
        return self.values.sum()

    def argmin(self) -> int:
        return numpy.argmin(self.values)

    def __getitem__(self, idx) -> float:
        return self.values[idx]

    def get_vacuum(self, threshold: float = 1e-3):
        nZ = len(self.values)

        z_min_charge_density_index = self.argmin()
        z_charge_density_value = self.values[z_min_charge_density_index]

        z_vacuum_max_index = z_vacuum_min_index = z_min_charge_density_index

        while numpy.abs(
                self.values[z_vacuum_max_index - int(z_vacuum_max_index / nZ) * nZ] - z_charge_density_value
        ) < threshold:
            z_vacuum_max_index += 1

        while numpy.abs(self.values[z_vacuum_min_index] - z_charge_density_value) < threshold:
            z_vacuum_min_index -= 1

        z_vacuum_center_index = int((z_vacuum_min_index + z_vacuum_max_index) / 2)
        if z_vacuum_center_index < 0:
            z_vacuum_center_index += nZ
        elif z_vacuum_center_index >= nZ:
            z_vacuum_center_index -= nZ

        return z_vacuum_min_index, z_vacuum_center_index, z_vacuum_max_index


class VaspResultGrid:
    """Vasp results given as one value on a grid of points"""

    def __init__(
        self,
        geometry: Geometry,
        grid_data: numpy.ndarray,
    ):
        self.geometry = geometry
        self.grid_data = grid_data

    @classmethod
    def from_file(cls, f: TextIO) -> 'VaspResultGrid':
        geometry = Geometry.from_poscar(f)

        # get points
        grid_size = tuple(int(x) for x in f.readline().split())
        num_points = grid_size[0] * grid_size[1] * grid_size[2]
        points = []

        remaining_lines = f.readlines()
        nlines = int(numpy.ceil(num_points / 5))

        for i in range(nlines):
            points.extend(float(x) for x in remaining_lines[i].split())

        # data are stored in the format (Z, Y, X), so it is reversed here:
        grid_data = numpy.array(points).reshape(tuple(reversed(grid_size))).T

        return cls(geometry, grid_data)

    def to_file(self, f: TextIO) -> None:
        self.geometry.to_poscar(f)

        f.write('\n {:4} {:4} {:4}\n'.format(*self.grid_data.shape))

        # use numpy.savetxt() for the rest, as it is (wayyyyy!!) faster
        num_points = self.grid_data.shape[0] * self.grid_data.shape[1] * self.grid_data.shape[2]

        num_lines = int(numpy.ceil(num_points / 5))

        data_to_write = numpy.zeros(num_lines * 5)
        data_to_write[0:num_points] = self.grid_data.T.ravel()
        data_to_write = data_to_write.reshape((num_lines, 5))

        numpy.savetxt(f, data_to_write, fmt='% .10e')

    def planar_average(self, axis: int) -> PlanarAverage:

        shape = self.grid_data.shape
        volume = numpy.prod(shape)

        axis_avg = []

        for i in range(shape[axis]):
            if axis == 0:
                avg = self.grid_data[i, :, :].sum()
            elif axis == 1:
                avg = self.grid_data[:, i, :].sum()
            else:
                avg = self.grid_data[:, :, i].sum()

            axis_avg.append(avg / (volume / shape[axis]))

        return PlanarAverage(numpy.array(axis_avg))

    def xy_planar_average(self) -> PlanarAverage:
        """Get an average of the value along Z"""

        return self.planar_average(2)


class VaspChgCar(VaspResultGrid):
    pass


class VaspLocPot(VaspResultGrid):
    pass
