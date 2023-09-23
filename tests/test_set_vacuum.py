from io import StringIO

import pytest

from ec_interface.vasp_geometry import Geometry

DUMMY_POSCAR = """Li slab (100) 1x1x7 + 15 ang vacuum
    1.000000000000000
     3.4351914121789999    0.0000000000000000    0.0000000000000000
     0.0000000000000000    3.4351914121789999    0.0000000000000000
     0.0000000000000000    0.0000000000000000   25.3055742365379999
   Li
     7
Selective dynamics
Direct
  0.5000000000000000  0.5000000000000000  0.2939135226810297   T   T   T
  0.0000000000000000 -0.0000000000000000  0.3655281817206787   T   T   T
  0.5000000000000000  0.5000000000000000  0.4317042303645421   T   T   T
  0.0000000000000000  0.0000000000000000  0.5000000000000000   F   F   F
  0.5000000000000000  0.5000000000000000  0.5682957696354574   T   T   T
  0.0000000000000000 -0.0000000000000000  0.6344718182793215   T   T   T
  0.5000000000000000  0.5000000000000000  0.7060864773189715   T   T   T
"""


def test_open_geometry():
    f = StringIO()
    f.write(DUMMY_POSCAR)
    f.seek(0)

    geometry = Geometry.from_poscar(f)

    assert geometry.ion_types == ['Li']
    assert geometry.ion_numbers == [7]
    assert geometry.positions.shape == (7, 3)
    assert geometry.is_direct


def test_change_vacuum():
    f = StringIO()
    f.write(DUMMY_POSCAR)
    f.seek(0)

    geometry = Geometry.from_poscar(f)

    assert geometry.slab_thickness() == pytest.approx(10.43, 0.01)
    assert geometry.interslab_distance() == pytest.approx(14.87, 0.01)

    new_geometry = geometry.change_interslab_distance(20.)

    assert new_geometry.slab_thickness() == pytest.approx(10.43, 0.01)  # slab size did not change
    assert new_geometry.interslab_distance() == pytest.approx(20.)  # distance did!
