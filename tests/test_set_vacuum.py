from io import StringIO

import pytest

from ec_interface.vasp_geometry import Geometry
from tests import DUMMY_POSCAR


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
