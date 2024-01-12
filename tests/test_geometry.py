import io
from io import StringIO

import numpy
import pytest
import pathlib

from ec_interface.vasp_geometry import Geometry, get_zvals
from ec_interface.molecular_geometry import MolecularGeometry
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


GEOMETRY = """3
Test
H 0.7 0.7 0.0
O 0.0 0.0 0.0
H 0.7 -0.7 0.0
"""


def test_read_molecular_geometry():
    f = StringIO()
    f.write(GEOMETRY)
    f.seek(0)
    molecular_geometry = MolecularGeometry.from_xyz(f)

    assert len(molecular_geometry) == 3
    assert molecular_geometry.symbols == ['H', 'O', 'H']
    assert numpy.allclose(molecular_geometry.positions, [[.7, .7, .0], [.0, .0, .0], [0.7, -.7, .0]])


def test_convert_molecular_geometry():

    lattice = numpy.array([
        [20., .0, .0],
        [.0, 20., .0],
        [.0, .0, 20.],
    ])

    with (pathlib.Path(__file__).parent / 'THF.xyz').open() as f:
        molecular_geometry = MolecularGeometry.from_xyz(f)

    vasp_geometry = molecular_geometry.to_vasp(lattice_vectors=lattice)

    assert numpy.allclose(vasp_geometry.lattice_vectors, lattice)
    assert molecular_geometry.symbols == vasp_geometry.ions
    assert numpy.allclose(vasp_geometry._cartesian_coordinates, molecular_geometry.positions)


def test_convert_molecular_sort():

    lattice = numpy.array([
        [20., .0, .0],
        [.0, 20., .0],
        [.0, .0, 20.],
    ])

    f = StringIO()
    f.write(GEOMETRY)
    f.seek(0)
    molecular_geometry = MolecularGeometry.from_xyz(f)

    vasp_geometry = molecular_geometry.to_vasp(lattice_vectors=lattice, sort=True)

    assert vasp_geometry.ions == ['H', 'H', 'O']


def test_convert_molecular_geometry_with_shift():

    lattice = numpy.array([
        [20., .0, .0],
        [.0, 20., .0],
        [.0, .0, 20.],
    ])

    shift = [.2, 5., -1]

    with (pathlib.Path(__file__).parent / 'THF.xyz').open() as f:
        molecular_geometry = MolecularGeometry.from_xyz(f)

    vasp_geometry = molecular_geometry.to_vasp(lattice_vectors=lattice, shift_positions=shift)
    assert numpy.allclose(vasp_geometry._cartesian_coordinates, molecular_geometry.positions + shift)


def test_merge():
    f = StringIO()
    f.write(DUMMY_POSCAR)
    f.seek(0)

    geometry = Geometry.from_poscar(f)

    lattice = numpy.array([
        [5., .0, .0],
        [.0, 5., .0],
        [.0, .0, 5.],
    ])

    f = StringIO()
    f.write(GEOMETRY)
    f.seek(0)
    additional = MolecularGeometry.from_xyz(f).to_vasp(lattice_vectors=lattice)

    new_geometry = geometry.merge_with(additional)

    assert numpy.allclose(new_geometry.lattice_vectors, geometry.lattice_vectors)
    assert new_geometry.ion_types == geometry.ion_types + additional.ion_types
    assert new_geometry.ion_numbers == geometry.ion_numbers + additional.ion_numbers

    assert numpy.allclose(new_geometry._cartesian_coordinates[:len(geometry)], geometry._cartesian_coordinates)
    assert numpy.allclose(new_geometry._cartesian_coordinates[len(geometry):], additional._cartesian_coordinates)

    assert numpy.array_equal(new_geometry.selective_dynamics[:len(geometry)], geometry.selective_dynamics)
