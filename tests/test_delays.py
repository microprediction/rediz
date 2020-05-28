from rediz.client import Rediz
import json, time
from rediz.rediz_test_config import REDIZ_TEST_CONFIG
import muid, pprint
from rediz.rediz_test_config_credentials import BELLEHOOD_BAT
import time

# rm tmp*.json; pip install -e . ; python -m pytest tests/test_delays.py ; cat tmp_delays.json

def dump(obj,name="delays.json"): # Debugging
    json.dump(obj,open("tmp_delays.json","w"))

def test_delay_real():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    do_test_delay_string(rdz)
    do_test_lags_and_delays(rdz)

def test_delay_fake():
    rdz = Rediz()
    do_test_delay_string(rdz)
    do_test_lags_and_delays(rdz)

def do_test_delay_string(rdz):
    assert 1 in rdz.DELAYS
    assert 5 in rdz.DELAYS
    NAME      = 'test-delay-c6bd-464c-asad-fe9.json'
    rdz._delete_implementation(NAME)
    time.sleep(0.1)
    WRITE_KEY = BELLEHOOD_BAT
    assert muid.validate(WRITE_KEY), "MUID NOT WORKING ?! "
    prctl = rdz.set( name = NAME,  value = "living in the past",  write_key=WRITE_KEY )
    time.sleep(3)
    prctl = rdz.set( name = NAME,  value = "living in the present",  write_key=WRITE_KEY )
    time.sleep(3)
    assert rdz.admin_promises()>0
    delayed_1_value = rdz.get_delayed(name=NAME,delay=1 )
    assert delayed_1_value=="living in the present"
    delayed_5_value = rdz.get_delayed(name=NAME,delay=5)
    assert delayed_5_value=="living in the past"

    budgets = rdz.get_budgets()
    budget  = rdz.get_budget(name=NAME)

    # Test market


    rdz._delete_implementation(NAME)


def do_test_lags_and_delays(rdz):
    assert 1 in rdz.DELAYS
    assert 5 in rdz.DELAYS
    NAME = 'test-delay-lags-c6bd-464c-fe9.json'
    rdz._delete_implementation(NAME)
    time.sleep(0.1)
    WRITE_KEY = BELLEHOOD_BAT
    prctl = rdz.set(name=NAME, value=6.0, write_key=WRITE_KEY)

    for _ in range(2):
        time.sleep(1)
        rdz.admin_promises()
    prctl = rdz.set(name=NAME, value=16.0, write_key=WRITE_KEY)
    time16 = time.time()
    prms = list()
    time.sleep(1.1)
    for _ in range(3):
        time.sleep(1)
        prms.append( rdz.admin_promises() )

    # Check delayed values
    delayed_1_value = rdz.get_delayed(name=NAME, delay=1)
    rdz.touch(name=NAME,write_key=WRITE_KEY)
    assert abs(float(delayed_1_value)-16.0)<1e-5
    delayed_5_value   = float(rdz.client.get(name=rdz.delayed_name(name=NAME,delay=5)))
    delayed_5_value_2 = rdz.get_delayed(name=NAME,delay=5)
    assert abs(delayed_5_value-delayed_5_value_2)<1e-5
    elapsed = time.time()-time16
    if elapsed<5:
        assert abs(float(delayed_5_value)-6.0)<1e-5
    else:
        assert abs(float(delayed_5_value)-16.0)<1e-5

    # Test lags while we are at it
    lagged_values = rdz.get_lagged_values(name=NAME)
    lagged_times  = rdz.get_lagged_times(name=NAME)
    lagged = rdz.get_lagged(name=NAME)
    lagged_values1 = rdz.get(rdz.LAGGED_VALUES+NAME)
    lagged_times1 = rdz.get(rdz.LAGGED_TIMES+NAME)
    assert all( [ abs(t1-t2)<1e-5 for t1,t2 in zip(lagged_times,lagged_times1) ] )
    assert all([abs(x1-x2) < 1e-5 for x1, x2 in zip(lagged_values, lagged_values1)])

    # Test market

    rdz._delete_implementation(NAME)


