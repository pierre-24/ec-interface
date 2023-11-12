import pathlib

import numpy
import pytest
import zipfile

from ec_interface.scripts import INPUT_NAME
from ec_interface.vasp_results import VaspLocPot
from ec_interface.ec_results import ECResults
from ec_interface.ec_parameters import ECParameters

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

    ec_parameters = ECParameters(21, 0, 0.01, step=0.01)
    ec_results = ECResults.from_calculations(ec_parameters, pathlib.Path.cwd())

    assert len(ec_results) == 1

    # check nelect
    assert ec_results.nelects[0] == nelect_inp

    # check fermi energy
    with (subdirectory / 'OUTCAR').open() as f:
        lines = f.readlines()
        for line in reversed(lines):
            if 'Fermi energy:' in line:
                assert float(line[-20:]) == pytest.approx(ec_results.fermi_energies[0])
                break

    # check free energy
    with (subdirectory / 'OSZICAR').open() as f:
        lines = f.readlines()
        chunks = lines[-2].split()
        assert float(chunks[4]) == pytest.approx(ec_results.free_energies[0])

    # check ref & avg potential
    with (subdirectory / 'LOCPOT').open() as f:
        local_potential = VaspLocPot.from_file(f)
        xy_avg = local_potential.xy_average()
        assert xy_avg[0] == pytest.approx(ec_results.vacuum_potentials[0])  # potential at z=0 is more or less the ref
        assert numpy.sum(xy_avg) / len(xy_avg) == pytest.approx(ec_results.average_potentials[0], abs=1e-3)  # average

    # check charge density (sum should be equal to total charge)
    with (subdirectory / 'charge_density_xy_avg.csv').open() as f:
        data = numpy.loadtxt(f)
        assert data[:, 1].sum() / 360 == pytest.approx(nelect_inp, 0.01)  # from chgcar
        assert data[:, 2].sum() == pytest.approx(nelect_inp, 0.01)  # charge at z-position
        assert data[-1, 3] == pytest.approx(nelect_inp, 0.01)  # cumulative sum


def test_compute_fee():
    ec_parameters = ECParameters(21, 0.1, 0.1, step=0.2, additional=[21.01, 21.09])

    # note: these data are more or less reproducing the ones found in 10.1021/acs.jctc.1c01237 for Li (100) with HBM
    ec_results = ECResults.from_hdf5(ec_parameters, pathlib.Path(pathlib.Path(__file__).parent / 'ec_results.h5'))

    assert ec_results.estimate_active_fraction() == pytest.approx(0.334, abs=.001)

    # get similar results with fermi and "ideal" approach
    data_hbm_fermi = ec_results.compute_fee_hbm_fermi()
    capacitance_hbm_fermi = -numpy.polyfit(data_hbm_fermi[:, 1], data_hbm_fermi[:, 2], 2)[0] * 2

    assert capacitance_hbm_fermi == pytest.approx(0.05, abs=0.01)

    data_hbm_ideal = ec_results.compute_fee_hbm(alpha=0.334)
    assert numpy.allclose(data_hbm_ideal[:, 2], data_hbm_fermi[:, 2], rtol=1e-3)

    capacitance_hbm_ideal = -numpy.polyfit(data_hbm_ideal[:, 1], data_hbm_ideal[:, 2], 2)[0] * 2
    assert capacitance_hbm_ideal == pytest.approx(capacitance_hbm_fermi, abs=0.001)

    # get something different (and larger!) with the estimated vacuum fraction
    data_hbm_vac = ec_results.compute_fee_hbm(alpha=0.59)
    capacitance_hbm_vac = -numpy.polyfit(data_hbm_vac[:, 1], data_hbm_vac[:, 2], 2)[0] * 2

    assert capacitance_hbm_vac == pytest.approx(0.09, abs=0.01)
    assert capacitance_hbm_vac != pytest.approx(capacitance_hbm_fermi, abs=0.001)
