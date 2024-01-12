import numpy
from typing import TextIO, List
from numpy.typing import NDArray

from ec_interface import vasp_geometry


class MolecularGeometry:
    """Molecular geometry, i.e., a geometry without any PBC
    """

    def __init__(self, symbols: List[str], positions: NDArray[float]):
        assert positions.shape == (len(symbols), 3)

        self.symbols = symbols
        self.positions = positions

    def __len__(self) -> int:
        return len(self.symbols)

    @classmethod
    def from_xyz(cls, f: TextIO) -> 'MolecularGeometry':
        """Read geometry from a XYZ file
        """

        symbols = []
        positions = []

        n = int(f.readline())
        f.readline()

        for i in range(n):
            data = f.readline().split()
            symbols.append(data[0])
            positions.append([float(x) for x in data[1:]])

        return cls(symbols, numpy.array(positions))

    def as_xyz(self, title: str = '') -> str:
        """Get XYZ representation of this geometry"""

        r = '{}\n{}'.format(len(self), title)
        for i in range(len(self)):
            r += '\n{:2} {: .7f} {: .7f} {: .7f}'.format(self.symbols[i], *self.positions[i])

        return r

    def to_vasp(
            self,
            lattice_vectors: NDArray,
            title: str = '',
            sort: bool = False,
            shift_positions: NDArray = None
    ) -> vasp_geometry.Geometry:
        """Convert to a VASP geometry"""

        symbols = self.symbols.copy()
        positions = self.positions.copy()

        # sort if any
        if sort:
            sorted_symbols = sorted(zip(symbols, range(len(self))))
            symbols = [x[0] for x in sorted_symbols]
            positions = positions[list(x[1] for x in sorted_symbols), :]

        # count ions
        ions_types, ions_numbers = vasp_geometry.count_ions(symbols)

        # shift if any
        if shift_positions is not None:
            positions += shift_positions

        return vasp_geometry.Geometry(
            title=title,
            lattice_vectors=lattice_vectors,
            ion_types=ions_types,
            ion_numbers=ions_numbers,
            positions=positions,
            is_direct=False
        )
