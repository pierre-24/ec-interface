import numpy

from typing import List, TextIO, Dict, Tuple


def get_zvals(f: TextIO) -> Dict[str, float]:
    """Extract the number of valence electron in a POTCAR file
    """
    lines = f.readlines()
    zvals = {}

    current_element = None
    for line in lines:
        if 'VRHFIN' in line:
            current_element = line[line.find('=') + 1:line.find(':')]
        if 'ZVAL' in line:
            start = line.find('ZVAL')
            start = line.find('=', start)
            value = float(line[start + 1:start + 8])

            zvals[current_element] = value

    return zvals


def count_ions(symbols: List[str]) -> Tuple[List[str], List[int]]:
    """Count ions in VASP style (i.e., get a pair `ion_types, ion_numbers` from `symbols`)
    """

    ions_types = []
    ions_numbers = []

    if len(symbols) > 0:
        current_ion = symbols[0]
        current_number = 1
        for symbol in symbols[1:]:
            if symbol == current_ion:
                current_number += 1
            else:
                ions_types.append(current_ion)
                ions_numbers.append(current_number)
                current_ion = symbol
                current_number = 1

        # add last:
        ions_types.append(current_ion)
        ions_numbers.append(current_number)

    return ions_types, ions_numbers


class Geometry:
    def __init__(
        self,
        title: str,
        lattice_vectors: numpy.ndarray,
        ion_types: List[str],
        ion_numbers: List[int],
        positions: numpy.ndarray,
        is_direct: bool = True,
        selective_dynamics: numpy.array = None
    ):
        self.title = title
        self.lattice_vectors = lattice_vectors
        self.ion_types = ion_types
        self.ion_numbers = ion_numbers
        self.selective_dynamics = selective_dynamics

        self.ions = []
        for ion_type, ion_number in zip(ion_types, ion_numbers):
            self.ions.extend([ion_type] * ion_number)

        self._cartesian_coordinates = None
        self._direct_coordinates = None

        if is_direct:
            self._direct_coordinates = positions.copy()
            self._cartesian_coordinates = numpy.einsum('ij,jk->ik', positions, self.lattice_vectors)
        else:
            self._cartesian_coordinates = positions.copy()
            self._direct_coordinates = numpy.einsum('ij,jk->ik', positions, numpy.linalg.inv(self.lattice_vectors))

    def __len__(self):
        return sum(self.ion_numbers)

    def __str__(self) -> str:
        return self.as_poscar()

    def as_poscar(self, direct: bool = True) -> str:
        """Get a representation as in a POSCAR, using direct coordinates or not.
        """

        r = '{}\n1.0\n'.format(self.title)
        r += '\n'.join('{: 16.12f} {: 16.12f} {: 16.12f}'.format(*self.lattice_vectors[i]) for i in range(3))
        r += '\n{}\n{}\n'.format(' '.join(self.ion_types), ' '.join(str(x) for x in self.ion_numbers))

        if self.selective_dynamics is not None:
            r += 'Selective dynamics\n'

        if direct:
            r += 'Direct\n'
            p = self._direct_coordinates
        else:
            r += 'Carthesian\n'
            p = self._cartesian_coordinates

        for i in range(len(self)):
            r += '{: 16.12f} {: 16.12f} {: 16.12f}'.format(*p[i])
            if self.selective_dynamics is not None:
                r += ' {} {} {}'.format(*('T' if x else 'F' for x in self.selective_dynamics[i]))

            r += ' {}\n'.format(self.ions[i])

        return r

    def to_poscar(self, f: TextIO, direct: bool = True):
        """Write a POSCAR in `f`
        """
        f.write(self.as_poscar(direct=direct))

    @classmethod
    def from_poscar(cls, f: TextIO):
        title = f.readline().strip()

        # get lattice vectors
        scaling = float(f.readline())
        lattice_vectors = scaling * numpy.array([[float(x) for x in f.readline().split()] for _ in range(3)])

        ion_types = f.readline().split()
        ion_numbers = [int(x) for x in f.readline().split()]

        line = f.readline().strip()[0].lower()
        is_selective_dynamics = line == 's'

        if is_selective_dynamics:
            is_direct = f.readline().strip()[0].lower() == 'd'
        else:
            is_direct = line == 'd'

        # get geometry
        geometry = []
        selective_dynamics = []
        line = f.readline()
        for i in range(sum(ion_numbers)):
            chunks = line.split()
            geometry.append([float(x) for x in chunks[:3]])
            if is_selective_dynamics:
                selective_dynamics.append([x == 'T' for x in chunks[3:6]])

            line = f.readline()

        positions = numpy.array(geometry)
        selective_dynamics_arr = None
        if is_selective_dynamics:
            selective_dynamics_arr = numpy.array(selective_dynamics, dtype=bool)

        return cls(
            title,
            lattice_vectors,
            ion_types,
            ion_numbers,
            positions,
            is_direct=is_direct,
            selective_dynamics=selective_dynamics_arr
        )

    def cartesian_coordinates(self) -> numpy.ndarray:
        """Convert to cartesian coordinates if any
        """

        return self._cartesian_coordinates

    def direct_coordinates(self) -> numpy.ndarray:
        """Convert to cartesian coordinates if any
        """

        return self._direct_coordinates

    def interslab_distance(self) -> float:
        """Assume that the geometry is a slab and compute the interslab distance
        """

        z_coo = self.cartesian_coordinates()[:, 2]
        return z_coo.min() - z_coo.max() + self.lattice_vectors[2, 2]

    def slab_thickness(self) -> float:
        """Assume that the geometry is a slab (along z) and compute the thickness of said slab
        """

        z_coo = self.cartesian_coordinates()[:, 2]
        return z_coo.max() - z_coo.min()

    def change_interslab_distance(self, d: float, direct: bool = True) -> 'Geometry':
        """Assume that the geometry is a slab (along z) and change interslab distance (c axis).
        """

        z_positions = self.cartesian_coordinates()[:, 2]

        # set at zero:
        z_positions -= numpy.min(z_positions)

        # get slab size
        slab_size = numpy.max(z_positions)

        # get corresponding lattice_vector
        z_lattice_norm = slab_size + d

        # re-center slab
        z_positions += d / 2

        # create a new geometry
        if direct:
            p = self._direct_coordinates.copy()
            p[:, 2] = z_positions / z_lattice_norm
        else:
            p = self._cartesian_coordinates.copy()
            p[:, 2] = z_positions

        new_lattice_vectors = self.lattice_vectors.copy()
        new_lattice_vectors[2] = [.0, .0, z_lattice_norm]

        return Geometry(
            self.title,
            new_lattice_vectors,
            self.ion_types,
            self.ion_numbers,
            p,
            is_direct=direct,
            selective_dynamics=self.selective_dynamics
        )

    def nelect(self, f: TextIO) -> float:
        """Read out the number of valence electrons from a POTCAR (`f`)
        and compute the corresponding number of electrons in the system.
        """
        zvals = get_zvals(f)
        nelect = 0
        for n, symbol in zip(self.ion_numbers, self.ion_types):
            nelect += n * zvals[symbol]

        return nelect
