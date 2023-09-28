import io
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
