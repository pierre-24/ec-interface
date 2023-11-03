import pathlib

import numpy
import pytest
import zipfile

from ec_interface.scripts import INPUT_NAME
from ec_interface.vasp_results import VaspLocPot
from ec_interface.scripts.extract_data import extract_data_from_directory

from tests import DUMMY_EC_INPUT


@pytest.fixture
def basic_inputs(tmp_path, monkeypatch):
    """Create basic inputs"""

    # ec input
    with (tmp_path / INPUT_NAME).open('w') as f:
        f.write(DUMMY_EC_INPUT)

    # extract zipfile
    with zipfile.ZipFile(pathlib.Path(__file__).parent / 'EC_20.990.zip') as f:
        f.extractall(tmp_path)

    # set chdir, so that everything happens within temporary directory
    monkeypatch.chdir(tmp_path)


def test_extract_data(basic_inputs):
    nelect_inp = 20.99
    subdirectory = pathlib.Path('EC_{:.3f}'.format(nelect_inp))
    assert subdirectory.exists()

    nelect, free_energy, fermi_energy, vacuum_pot, avg_pot = extract_data_from_directory(subdirectory)

    # check nelect
    assert nelect == nelect_inp

    # check fermi energy
    with (subdirectory / 'OUTCAR').open() as f:
        lines = f.readlines()
        for line in reversed(lines):
            if 'Fermi energy:' in line:
                assert float(line[-20:]) == pytest.approx(fermi_energy)
                break

    # check free energy
    with (subdirectory / 'OSZICAR').open() as f:
        lines = f.readlines()
        chunks = lines[-2].split()
        assert float(chunks[4]) == pytest.approx(free_energy)

    # check ref & avg potential
    with (subdirectory / 'LOCPOT').open() as f:
        local_potential = VaspLocPot.from_file(f)
        xy_avg = local_potential.xy_average()
        assert xy_avg[0] == pytest.approx(vacuum_pot)  # potential at z=0 is more or less the ref
        assert numpy.sum(xy_avg) / 25.305 == pytest.approx(avg_pot, abs=1e-3)  # average

    # check charge density (sum should be equal to total charge)
    with (subdirectory / 'charge_density_xy_avg.csv').open() as f:
        data = numpy.loadtxt(f)
        assert data[:, 1].sum() / 360 == pytest.approx(nelect, 0.01)  # from chgcar
        assert data[:, 2].sum() == pytest.approx(nelect, 0.01)  # charge at z-position
        assert data[-1, 3] == pytest.approx(nelect, 0.01)  # cumulative sum
