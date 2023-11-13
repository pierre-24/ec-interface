import pathlib

import pytest

from ec_interface.ec_parameters import ECParameters
from ec_interface.scripts import INPUT_NAME
from ec_interface.scripts.make_directories import create_input_directories

from tests import DUMMY_POSCAR, DUMMY_INCAR, DUMMY_KPOINTS, DUMMY_POTCAR, DUMMY_EC_INPUT


@pytest.fixture
def basic_inputs(tmp_path, monkeypatch):
    """Create basic inputs"""

    inputs = [
        ('INCAR', DUMMY_INCAR),
        ('POSCAR', DUMMY_POSCAR),
        ('POTCAR', DUMMY_POTCAR),
        ('KPOINTS', DUMMY_KPOINTS),
        (INPUT_NAME, DUMMY_EC_INPUT)
    ]

    for name, content in inputs:
        with (tmp_path / name).open('w') as f:
            f.write(content)

    # set chdir, so that everything happens within temporary directory
    monkeypatch.chdir(tmp_path)


def test_create_directories_ok(basic_inputs):
    with pathlib.Path(INPUT_NAME).open() as f:
        parameters = ECParameters.from_yaml(f)

    create_input_directories(parameters, use_symlinks=True)

    for i in range(-5, 6):
        nelect = 21. + i * 0.01

        # directory
        directory = pathlib.Path('EC_{:.3f}'.format(nelect))
        assert directory.exists()

        # symlinks
        symlinks = ['POTCAR', 'POSCAR', 'KPOINTS']
        for name in symlinks:
            assert (directory / name).exists()
            assert (directory / name).is_symlink()

        # INCAR:
        with (directory / 'INCAR').open() as f:
            incar_content = f.read()
            assert 'NELECT = {:.3f}'.format(nelect) in incar_content


def test_create_directories_missing_files_ko(basic_inputs):
    with pathlib.Path(INPUT_NAME).open() as f:
        parameters = ECParameters.from_yaml(f)

    cwd = pathlib.Path.cwd()

    files = ['INCAR', 'POTCAR', 'POSCAR', 'KPOINTS']
    tmpfile = cwd / '.tmp'

    prev = None
    for name in files:
        with pytest.raises(FileNotFoundError, match=name):
            if prev is not None:
                tmpfile.rename(prev)

            path = cwd / name
            assert path.exists()
            prev = path

            path.rename(tmpfile)
            create_input_directories(parameters, use_symlinks=True)


def test_create_directories_missing_in_incar_ko(basic_inputs):
    with pathlib.Path(INPUT_NAME).open() as f:
        parameters = ECParameters.from_yaml(f)

    cwd = pathlib.Path.cwd()
    lines = DUMMY_INCAR.splitlines()

    vars = ['LCHARG', 'LVHAR', 'LVTOT']
    for var in vars:
        with (cwd / 'INCAR').open('w') as f:
            for line in lines:
                if var not in line:
                    f.write(line)

        with pytest.raises(Exception, match=var):
            create_input_directories(parameters, use_symlinks=True)
