import pathlib

import pytest
import yaml

from ec_interface.scripts import INPUT_NAME
from ec_interface.ec_parameters import ECParameters
from ec_interface.scripts.make_directories import create_input_directories

DUMMY_INCAR = """
ENCUT = 520.000000
ALGO = Fast
LREAL = Auto
LCHARG = .TRUE.
LVHAR = .TRUE.
LVTOT = .TRUE.
LSOL = .TRUE.
EB_K = 78.360000
TAU = 0.000000
LAMBDA_D_K = 3.040000
"""

DUMMY_KPOINTS = """K-Points
 0
Monkhorst Pack
 8  8  1
 0  0  0
"""

DUMMY_POSCAR = """Pt
   1.00000000000000
     5.6416157960000008    0.0000000000000000    0.0000000000000000
     2.8208078980000004    4.8857825977275668    0.0000000000000000
     0.0000000000000000    0.0000000000000000   21.9095400125127817
   Pt
    16
Selective dynamics
Direct
  0.0000000000000000  0.0000000000000000  0.3427243190829614   T   T   T
  0.5000000000000000  0.0000000000000000  0.3427243190829614   T   T   T
  0.0000000000000000  0.5000000000000000  0.3427243190829614   T   T   T
  0.5000000000000000  0.5000000000000000  0.3427243190829614   T   T   T
  0.1666666666666643  0.1666666666666643  0.4474388781586569   F   F   F
  0.6666666666666643  0.1666666666666643  0.4474388781586569   F   F   F
  0.1666666666666643  0.6666666666666643  0.4474388781586569   F   F   F
  0.6666666666666643  0.6666666666666643  0.4474388781586569   F   F   F
  0.8333333333333357  0.3333333333333357  0.5525611218413431   F   F   F
  0.3333333333333357  0.3333333333333357  0.5525611218413431   F   F   F
  0.8333333333333357  0.8333333333333357  0.5525611218413431   F   F   F
  0.3333333333333357  0.8333333333333357  0.5525611218413431   F   F   F
  0.0000000000000000  0.0000000000000000  0.6572756809170386   T   T   T
  0.5000000000000000  0.0000000000000000  0.6572756809170386   T   T   T
  0.0000000000000000  0.5000000000000000  0.6572756809170386   T   T   T
  0.5000000000000000  0.5000000000000000  0.6572756809170386   T   T   T
"""

DUMMY_POTCAR = """
***REDACTED***
"""

DUMMY_EC_INPUT = """
ne_zc: 160.0
ne_added: 0.2
ne_removed: 0.2
step: 0.04
"""


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


def test_read_valid_ec_input_ok(basic_inputs):
    ec_parameters = dict(ne_zc=2., ne_added=0.4, ne_removed=0.2, step=0.01)

    with pathlib.Path(INPUT_NAME).open('w') as f:
        f.write(yaml.dump(ec_parameters, Dumper=yaml.Dumper))

    with pathlib.Path(INPUT_NAME).open() as f:
        ec_parms = ECParameters.from_yaml(f)

    assert ec_parms.ne_zc == ec_parameters['ne_zc']
    assert ec_parms.ne_added == ec_parameters['ne_added']
    assert ec_parms.ne_removed == ec_parameters['ne_removed']
    assert ec_parms.step == ec_parameters['step']


def test_create_directories_ok(basic_inputs):
    create_input_directories(pathlib.Path.cwd(), use_symlinks=True)

    for i in range(-5, 6):
        nelect = 160. + i * 0.04

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
    cwd = pathlib.Path.cwd()

    files = ['INCAR', 'POTCAR', 'POSCAR', 'KPOINTS', INPUT_NAME]
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
            create_input_directories(cwd, use_symlinks=True)


def test_create_directories_missing_in_incar_ko(basic_inputs):
    cwd = pathlib.Path.cwd()
    lines = DUMMY_INCAR.splitlines()

    vars = ['LCHARG', 'LVHAR', 'LVTOT']
    for var in vars:
        with (cwd / 'INCAR').open('w') as f:
            for line in lines:
                if var not in line:
                    f.write(line)

        with pytest.raises(Exception, match=var):
            create_input_directories(cwd, use_symlinks=True)
