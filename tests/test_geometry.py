import io
from io import StringIO

import numpy
import pytest

from ec_interface.vasp_geometry import Geometry, get_zvals
from tests import DUMMY_POSCAR, DUMMY_POTCAR


def test_open_geometry():
    f = StringIO()
    f.write(DUMMY_POSCAR)
    f.seek(0)

    geometry = Geometry.from_poscar(f)

    assert geometry.ion_types == ['Li']
    assert geometry.ion_numbers == [7]
    assert geometry._cartesian_coordinates.shape == (7, 3)


def test_direct_to_cartesian():
    cell = numpy.array([
        [3., 0., 0.],
        [1.5, 3., 0.],
        [.25, .25, 5.]
    ])

    direct_coos = numpy.array([
        [.5, .25, 0.],
        [.75, .5, .25],
        [.5, .75, .5],
        [.25, .5, .75],
    ])

    f = StringIO()

    geometry_from_direct = Geometry('test', cell, ['C'], [4, ], direct_coos, True)
    assert numpy.allclose(geometry_from_direct._direct_coordinates, direct_coos)

    geometry_from_direct.to_poscar(f, direct=False)
    f.seek(0)

    geometry_from_cartesian = Geometry.from_poscar(f)
    assert numpy.allclose(geometry_from_cartesian._direct_coordinates, direct_coos)


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


def test_nelect():
    f = StringIO()
    f.write(DUMMY_POSCAR)
    f.seek(0)

    geometry = Geometry.from_poscar(f)

    f = io.StringIO()
    f.write(DUMMY_POTCAR)
    f.seek(0)

    assert geometry.nelect(f) == 7.0


# a POTCAR with a bit more possibilities
DUMMY_POTCAR2 = """
   VRHFIN =Li: s1p0
   POMASS =    7.010; ZVAL   =    1.000    mass and valenz
   VRHFIN =C: s2p2
   POMASS =   12.011; ZVAL   =    4.000    mass and valenz
   VRHFIN =O: s2p4
   POMASS =   16.000; ZVAL   =    6.000    mass and valenz
   VRHFIN =H: ultrasoft test
   POMASS =    1.000; ZVAL   =    1.000    mass and valen
"""


def test_get_zvals():
    f = io.StringIO()
    f.write(DUMMY_POTCAR2)
    f.seek(0)

    zvals = get_zvals(f)
    assert zvals['H'] == 1.0
    assert zvals['Li'] == 1.0
    assert zvals['C'] == 4.0
    assert zvals['O'] == 6.0
