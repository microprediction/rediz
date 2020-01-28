from rediz.client import Rediz
from threezaconventions.crypto import random_key
import json, os, uuid, random, time
from rediz.rediz_test_config import REDIZ_TEST_CONFIG


def dump(obj,name="propagation.json"): # Debugging
    json.dump(obj,open("tmp_propagation.json","w"))

def test_propagation():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    PUBLISHER   = 'PUBLISHER_3b4e229a-ffb4-4fc2-8370-c147944aa2b.json'
    SUBSCRIBER  = 'SUBSCRIBER_ed2b4f6-c6bd-464c-a9e9-322e0c3147.json'
    PUBLISHER_write_key   = "b0b5753b-14e6-4051-b13e-132bb13ed1a9"
    SUBSCRIBER_write_key  = "caa09e4a-3901-4cdf-8301-774184e584f3"
    assert rdz.set( name = SUBSCRIBER, value = "some value",  write_key=SUBSCRIBER_write_key )
    assert rdz.set( name = SUBSCRIBER, value = "some value",       write_key=SUBSCRIBER_write_key )
    assert rdz.set( name = PUBLISHER,  value = "some other value", write_key=PUBLISHER_write_key )
    rdz._subscribe( publisher = PUBLISHER, subscriber = SUBSCRIBER )
    assert rdz.set( name = PUBLISHER, value = "some new value",    write_key=PUBLISHER_write_key )
    SUBSCRIBER_mailbox    = rdz.MESSAGES+SUBSCRIBER
    message_to_SUBSCRIBER = rdz.client.hget( SUBSCRIBER_mailbox, PUBLISHER )
    assert message_to_SUBSCRIBER=="some new value"

def test_delay():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    NAME      = 'test-delay-c6bd-464c-asad-fe9.json'
    WRITE_KEY = "6d77759b-685a-4e25-b75b-6619bf1f1119"
    assert rdz.set( name = NAME,  value = "living in the past",  write_key=WRITE_KEY )
    time.sleep(4)
    assert rdz.set( name = NAME,  value = "living in the present",  write_key=WRITE_KEY )
    time.sleep(2)
    assert rdz.admin_promises()>0

    delayed_value = rdz.client.get( rdz.DELAYED+"1"+rdz.SEP+NAME )
    assert delayed_value=="living in the present"
    delayed_value = rdz.client.get( rdz.DELAYED+"5"+rdz.SEP+NAME )
    assert delayed_value=="living in the past"
