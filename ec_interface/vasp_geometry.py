import numpy

from typing import List, TextIO


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
        self.positions = positions
        self.is_direct = is_direct
        self.selective_dynamics = selective_dynamics

        self.ions = []
        for ion_type, ion_number in zip(ion_types, ion_numbers):
            self.ions.extend([ion_type] * ion_number)

        self._cartesian_coordinates = None

    def __len__(self):
        return sum(self.ion_numbers)

    def __str__(self):
        r = '{}\n1.0\n'.format(self.title)
        r += '\n'.join('{: 16.12f} {: 16.12f} {: 16.12f}'.format(*self.lattice_vectors[i]) for i in range(3))
        r += '\n{}\n{}\n'.format(' '.join(self.ion_types), ' '.join(str(x) for x in self.ion_numbers))

        if self.selective_dynamics is not None:
            r += 'Selective dynamics\n'

        if self.is_direct:
            r += 'Direct\n'
        else:
            r += 'Carthesian\n'

        for i in range(len(self)):
            r += '{: 16.12f} {: 16.12f} {: 16.12f}'.format(*self.positions[i])
            if self.selective_dynamics is not None:
                r += ' {} {} {}'.format(*('T' if x else 'F' for x in self.selective_dynamics[i]))

            r += ' {}\n'.format(self.ions[i])

        return r

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
        if self._cartesian_coordinates is None:  # cache
            if self.is_direct:
                self._cartesian_coordinates = numpy.einsum('ij,jk->ij', self.positions, self.lattice_vectors)
            else:
                self._cartesian_coordinates = self.positions

        return self._cartesian_coordinates

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

    def change_interslab_distance(self, d: float) -> 'Geometry':
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
        new_positions = self.positions.copy()

        if self.is_direct:
            new_positions[:, 2] = z_positions / z_lattice_norm
        else:
            new_positions[:, 2] = z_positions

        new_lattice_vectors = self.lattice_vectors.copy()
        new_lattice_vectors[2] = [.0, .0, z_lattice_norm]

        return Geometry(
            self.title,
            new_lattice_vectors,
            self.ion_types,
            self.ion_numbers,
            new_positions,
            is_direct=self.is_direct,
            selective_dynamics=self.selective_dynamics
        )
