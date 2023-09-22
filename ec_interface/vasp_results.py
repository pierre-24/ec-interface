import pathlib
import h5py
import numpy
import math

from typing import TextIO, List


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
        lattice_vectors:
        numpy.ndarray,
        symbols: List[str],
        positions: numpy.ndarray,
        grid_data: numpy.ndarray,
        is_direct: bool = True
    ):
        self.lattice_vectors = lattice_vectors
        self.symbols = symbols
        self.positions = positions
        self.is_direct = is_direct
        self.grid_data = grid_data

    @classmethod
    def from_file(cls, f: TextIO):
        f.readline()  # skip title

        # get lattice vectors
        scaling = float(f.readline())
        lattice_vectors = scaling * numpy.array([[float(x) for x in f.readline().split()] for _ in range(3)])

        ion_types = f.readline().split()
        ion_numbers = [int(x) for x in f.readline().split()]  # skip ion numbers

        ions = []
        for ion_type, ion_number in zip(ion_types, ion_numbers):
            ions.extend([ion_type] * ion_number)

        is_direct = f.readline().strip()[0].lower() == 'd'

        # get geometry
        geometry = []
        line = f.readline()
        while line.strip() != '':
            geometry.append([float(x) for x in line.split()])
            line = f.readline()

        positions = numpy.array(geometry)

        # get points
        grid_size = tuple(int(x) for x in f.readline().split())
        num_points = grid_size[0] * grid_size[1] * grid_size[2]
        points = []

        remaining_lines = f.readlines()

        for i in range(int(math.ceil(num_points / 5))):
            points.extend(float(x) for x in remaining_lines[i].split())

        # data are stored in the format (Z, Y, X), so it is reversed here:
        grid_data = numpy.array(points).reshape(tuple(reversed(grid_size))).T

        return cls(lattice_vectors, ions, positions, grid_data, is_direct=is_direct)

    def xy_average(self) -> List[float]:
        """Get an average of the value along Z"""

        nX, nY, nZ = self.grid_data.shape
        xy_avg = []

        for i in range(nZ):
            xy_avg.append(self.grid_data[:, :, i].sum() / (nX * nY))

        return xy_avg


class VaspChgCar(VaspResultGrid):
    pass


class VaspLocPot(VaspResultGrid):
    pass