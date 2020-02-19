from rediz.client import Rediz
import json, os, uuid, random, time
from rediz.rediz_test_config import REDIZ_TEST_CONFIG

# rm tmp*.json; pip install -e . ; python -m pytest tests/test_delays.py ; cat tmp_delays.json

def dump(obj,name="delays.json"): # Debugging
    json.dump(obj,open("tmp_delays.json","w"))

def test_delay_real():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    do_test_delay(rdz)
    do_test_lags_and_delays(rdz)

def test_delay_fake():
    rdz = Rediz()
    do_test_delay(rdz)
    do_test_lags_and_delays(rdz)

def do_test_delay(rdz):
    assert 1 in rdz.DELAYS
    assert 5 in rdz.DELAYS
    NAME      = 'test-delay-c6bd-464c-asad-fe9.json'
    rdz._delete_implementation(NAME)
    time.sleep(0.1)
    WRITE_KEY = "6d77759b-685a-4e25-b75b-6619bf1f1119"
    prctl = rdz.set( name = NAME,  value = "living in the past",  write_key=WRITE_KEY )
    time.sleep(4)
    prctl = rdz.set( name = NAME,  value = "living in the present",  write_key=WRITE_KEY )
    time.sleep(3)
    assert rdz.admin_promises()>0
    delayed_value = rdz.get_delayed(name=NAME,delay=1 )
    assert delayed_value=="living in the present"
    delayed_value = rdz.client.get( name=rdz.DELAYED+"5"+rdz.SEP+NAME )
    assert delayed_value=="living in the past"

    # Test market


    rdz._delete_implementation(NAME)


def do_test_lags_and_delays(rdz):
    assert 1 in rdz.DELAYS
    assert 5 in rdz.DELAYS
    NAME = 'test-delay-lags-c6bd-464c-fe9.json'
    rdz._delete_implementation(NAME)
    time.sleep(0.1)
    WRITE_KEY = "6d77759b-685a-4e25-b75b-6619bf1f1119"
    prctl = rdz.set(name=NAME, value=6.0, write_key=WRITE_KEY)
    time.sleep(4)
    prctl = rdz.set(name=NAME, value=16.0, write_key=WRITE_KEY)
    time.sleep(3)
    rdz.admin_promises()
    delayed_value = rdz.get_delayed(name=NAME, delay=1)
    rdz.touch(name=NAME)
    assert abs(float(delayed_value)-16.0)<1e-5
    delayed_value = rdz.client.get(name=rdz.DELAYED + "5" + rdz.SEP + NAME)
    assert abs(float(delayed_value)-6.0)<1e-5
    lagged_values = rdz.get_lagged_values(name=NAME)
    lagged_times  = rdz.get_lagged_times(name=NAME)
    lagged = rdz.get_lagged(name=NAME)
    lagged_values1 = rdz.get(rdz.LAGGED_VALUES+NAME)
    lagged_times1 = rdz.get(rdz.LAGGED_TIMES+NAME)
    assert all( [ abs(t1-t2)<1e-5 for t1,t2 in zip(lagged_times,lagged_times1) ] )
    assert all([abs(x1-x2) < 1e-5 for x1, x2 in zip(lagged_values, lagged_values1)])

    # Test market

    rdz._delete_implementation(NAME)


