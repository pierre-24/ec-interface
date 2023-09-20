import pathlib
import h5py


class VaspResults:
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
