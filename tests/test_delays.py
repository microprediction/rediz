from rediz.client import Rediz
import json, time
from rediz.rediz_test_config import REDIZ_TEST_CONFIG, REDIZ_FAKE_CONFIG
BELLEHOOD_BAT = REDIZ_TEST_CONFIG['BELLEHOOD_BAT']

# rm tmp*.json; pip install -e . ; python -m pytest tests/test_delays.py ; cat tmp_delays.json

def dump(obj,name="delays.json"): # Debugging
    json.dump(obj,open("tmp_delays.json","w"))

def test_delay_real():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    do_test_delay_string(rdz)
    do_test_lags_and_delays(rdz)

def test_delay_fake():
    rdz = Rediz(**REDIZ_FAKE_CONFIG)
    do_test_delay_string(rdz)
    do_test_lags_and_delays(rdz)

def do_test_delay_string(rdz):
    assert 1 in rdz.DELAYS
    assert 5 in rdz.DELAYS
    NAME      = 'test-delay-c6bd-464c-asad-fe9.json'
    rdz._delete_implementation(NAME)
    time.sleep(0.1)
    WRITE_KEY = BELLEHOOD_BAT
    assert Rediz.safe_difficulty(write_key=WRITE_KEY) > 5, "MUID NOT WORKING ?! "
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

    # Timeline of writes
    #
    #       0          3s         5.5s
    # ------|----------|----------|--
    #       6         16          |
    #                             |
    # Lag 1 read                 16
    # Lag 5 read                  6

    # We write the value 6.0, then wait 3 seconds
    time6 = time.time()
    res1 = rdz.set(name=NAME, value=6.0, write_key=WRITE_KEY)
    assert 'value' in res1
    rdz.admin_promises()
    while time.time()-time6<3:
        rdz.admin_promises()
        time.sleep(0.1)

    # Then write 16.0
    res2 = rdz.set(name=NAME, value=16.0, write_key=WRITE_KEY)
    assert 'value' in res2
    time16 = time.time()  # Time at which 16.0 was written


    # Wait another 3 seconds
    time.sleep(1)
    prms = list()
    while time.time()-time6<5.5:
        prms.append( rdz.admin_promises() )
        time.sleep(0.1)

    # Get the value that has been delayed by 1 second or more ... this should be 16.0
    delayed_1_value = rdz.get_delayed(name=NAME, delay=1)
    rdz.touch(name=NAME,write_key=WRITE_KEY)
    assert abs(float(delayed_1_value)-16.0)<1e-5

    # Get the value delayed by 5 seconds or more two different ways ... this should be 6.0
    elapsed1 = time.time() - time16  # Did less than 5 seconds elapse ... just checking

    delayed_5_value   = float(rdz.client.get(name=rdz.delayed_name(name=NAME,delay=5)))
    delayed_5_value_2 = rdz.get_delayed(name=NAME,delay=5)
    assert abs(delayed_5_value-delayed_5_value_2)<1e-5
    elapsed2 = time.time()-time16             # Did less than 5 seconds elapse ... just checking again
    if elapsed1<5 and elapsed2<5:
        assert abs(float(delayed_5_value)-6.0)<1e-5
    elif elapsed1>5 and elapsed2>5:
        assert abs(float(delayed_5_value)-16.0)<1e-5
    else:
        pass # Give up checking this time as there could be a race condition in test

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


