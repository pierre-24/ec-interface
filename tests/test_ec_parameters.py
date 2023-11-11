import io

import pytest
import yaml

from ec_interface.ec_parameters import ECParameters


def test_read_valid_ec_input_ok():
    f = io.StringIO()
    ec_parameters = dict(ne_zc=2., ne_added=0.4, ne_removed=0.2, step=0.01)
    f.write(yaml.dump(ec_parameters, Dumper=yaml.Dumper))
    f.seek(0)

    ec_parms = ECParameters.from_yaml(f)

    assert ec_parms.ne_zc == ec_parameters['ne_zc']
    assert ec_parms.ne_added == ec_parameters['ne_added']
    assert ec_parms.ne_removed == ec_parameters['ne_removed']
    assert ec_parms.step == ec_parameters['step']


def test_steps_ok():

    # no additionals
    assert list(
        ECParameters(ne_zc=1.0, ne_added=0.2, ne_removed=0.2, step=0.1).steps()
    ) == pytest.approx([0.8, 0.9, 1.0, 1.1, 1.2])

    # additional is a step
    assert list(
        ECParameters(ne_zc=1.0, ne_added=0.2, ne_removed=0.2, step=0.1, additional=[1.1]).steps()
    ) == pytest.approx([0.8, 0.9, 1.0, 1.1, 1.2])

    # additional at the end
    assert list(
        ECParameters(ne_zc=1.0, ne_added=0.2, ne_removed=0.2, step=0.1, additional=[1.4]).steps()
    ) == pytest.approx([0.8, 0.9, 1.0, 1.1, 1.2, 1.4])

    # additional inside
    assert list(
        ECParameters(ne_zc=1.0, ne_added=0.2, ne_removed=0.2, step=0.1, additional=[1.05]).steps()
    ) == pytest.approx([0.8, 0.9, 1.0, 1.05, 1.1, 1.2])

    # (non-sorted) additionals inside
    assert list(
        ECParameters(ne_zc=1.0, ne_added=0.2, ne_removed=0.2, step=0.1, additional=[1.05, 0.85]).steps()
    ) == pytest.approx([0.8, 0.85, 0.9, 1.0, 1.05, 1.1, 1.2])

    # same additional
    assert list(
        ECParameters(ne_zc=1.0, ne_added=0.2, ne_removed=0.2, step=0.1, additional=[0.85, 0.85]).steps()
    ) == pytest.approx([0.8, 0.85, 0.9, 1.0, 1.1, 1.2])

    # additional at the beginning
    assert list(
        ECParameters(ne_zc=1.0, ne_added=0.2, ne_removed=0.2, step=0.1, additional=[0.7]).steps()
    ) == pytest.approx([0.7, 0.8, 0.9, 1.0, 1.1, 1.2])

    # all together
    assert list(
        ECParameters(ne_zc=1.0, ne_added=0.2, ne_removed=0.2, step=0.1, additional=[1.1, 1.4, 0.7, 0.85, 1.4]).steps()
    ) == pytest.approx([0.7, 0.8, 0.85, 0.9, 1.0, 1.1, 1.2, 1.4])
