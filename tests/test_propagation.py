from rediz.client import Rediz
from threezaconventions.crypto import random_key
import json, os, uuid, random, time
from rediz.rediz_test_config import REDIZ_TEST_CONFIG


def dump(obj,name="propagation.json"): # Debugging
    json.dump(obj,open("tmp_propagation.json","w"))

PARENT = 'parent_3b4e229a-ffb4-4fc2-8370-c147944aaa2b.json'
CHILD  = 'child_ed2b4f64-c6bd-464c-a9e9-322e2e0c3147.json'
PARENT_write_key = "d6e4d4d4-b8fc-4300-a55b-a99eab277443"
CHILD_write_key  = "eeecc61e-276e-487b-81d3-292c01ae66b6"

def test_propagation():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    rdz.set( name = CHILD,  value = "child value",  write_key=CHILD_write_key )
    rdz.set( name = PARENT, value = "parent value", write_key=PARENT_write_key )
    rdz._subscribe( publisher = PARENT, subscriber = CHILD )
    rdz.set( name = PARENT, value = "parent changed value", write_key=PARENT_write_key )
    CHILD_mailbox = rdz.MESSAGES+CHILD
    message_to_child = rdz.client.hget( CHILD_mailbox, PARENT )
    assert message_to_child=="parent changed value"

def test_delay():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    rdz.set( name = CHILD,  value = "expect to see me",  write_key=CHILD_write_key )
    time.sleep(1)
    assert rdz.admin_promises()>0
    
    delayed_value = rdz.client.get(rdz.DELAYED+CHILD )
    assert delayed_value=="expect to see me"
