from rediz.client import Rediz
from threezaconventions.crypto import random_key
import json, os, uuid, random, time
from rediz.rediz_test_config import REDIZ_TEST_CONFIG


def dump(obj,name="delays.json"): # Debugging
    json.dump(obj,open("tmp_delays.json","w"))


def test_delay():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    assert 1 in rdz.DELAY_SECONDS
    assert 5 in rdz.DELAY_SECONDS
    NAME      = 'test-delay-c6bd-464c-asad-fe9.json'
    rdz._delete(NAME)
    time.sleep(0.1)
    WRITE_KEY = "6d77759b-685a-4e25-b75b-6619bf1f1119"
    assert rdz.set( name = NAME,  value = "living in the past",  write_key=WRITE_KEY )==1
    time.sleep(4)
    assert rdz.set( name = NAME,  value = "living in the present",  write_key=WRITE_KEY )==1
    time.sleep(2)
    assert rdz.admin_promises()>0
    delayed_value = rdz.client.get( name=rdz.DELAYED+"1"+rdz.SEP+NAME )
    assert delayed_value=="living in the present"
    delayed_value = rdz.client.get( name=rdz.DELAYED+"5"+rdz.SEP+NAME )
    assert delayed_value=="living in the past"
    rdz._delete(NAME)