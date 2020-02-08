from rediz.client import Rediz
import json, os, uuid, random, time
from rediz.rediz_test_config import REDIZ_TEST_CONFIG

# rm tmp*.json; pip install -e . ; python -m pytest tests/test_delays.py ; cat tmp_delays.json

def dump(obj,name="delays.json"): # Debugging
    json.dump(obj,open("tmp_delays.json","w"))

def test_delay_real():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    do_test_delay(rdz)

def test_delay_fake():
    rdz = Rediz()
    do_test_delay(rdz)

def do_test_delay(rdz):
    assert 1 in rdz.DELAYS
    assert 5 in rdz.DELAYS
    NAME      = 'test-delay-c6bd-464c-asad-fe9.json'
    rdz._delete_implementation(NAME)
    time.sleep(0.1)
    WRITE_KEY = "6d77759b-685a-4e25-b75b-6619bf1f1119"
    assert rdz.set( name = NAME,  value = "living in the past",  write_key=WRITE_KEY )==1
    time.sleep(4)
    assert rdz.set( name = NAME,  value = "living in the present",  write_key=WRITE_KEY )==1
    time.sleep(3)
    assert rdz.admin_promises()>0
    delayed_value = rdz.get_delayed(name=NAME,delay=1 )
    assert delayed_value=="living in the present"
    delayed_value = rdz.client.get( name=rdz.DELAYED+"5"+rdz.SEP+NAME )
    assert delayed_value=="living in the past"

    # Test market

    


    rdz._delete_implementation(NAME)
