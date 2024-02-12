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

    def xy_average(self) -> NDArray:
        """Get an average of the value along Z"""

        nX, nY, nZ = self.grid_data.shape
        xy_avg = []

        for i in range(nZ):
            xy_avg.append(self.grid_data[:, :, i].sum() / (nX * nY))

        return numpy.array(xy_avg)


class VaspChgCar(VaspResultGrid):
    pass


class VaspLocPot(VaspResultGrid):
    pass
