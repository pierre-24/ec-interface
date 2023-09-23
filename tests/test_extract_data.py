import pathlib

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

    nelect, free_energy, fermi_energy, ref_potential = extract_data_from_directory(subdirectory)

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

    # check ref potential
    with (subdirectory / 'LOCPOT').open() as f:
        local_potential = VaspLocPot.from_file(f)
        xy_avg = local_potential.xy_average()
        assert xy_avg[0] == pytest.approx(ref_potential)  # potential at z=0 is more or less the ref
