from rediz.client import Rediz, default_is_valid_name, default_is_valid_key
from threezaconventions.crypto import random_key
import json, os, uuid, random, time
from rediz.rediz_test_config import REDIZ_TEST_CONFIG


def dump(obj,name="propagation.json"):
    json.dump(obj,open("propagation.json","w"))

def test_propagation():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    PARENT = 'parent_3b4e229a-ffb4-4fc2-8370-c147944aaa2b.json'
    CHILD  = 'child_ed2b4f64-c6bd-464c-a9e9-322e2e0c3147.json'
    PARENT_write_key = "d6e4d4d4-b8fc-4300-a55b-a99eab277443"
    CHILD_write_key  = "eeecc61e-276e-487b-81d3-292c01ae66b6"
    execution_log = rdz.set( name = CHILD,  value = "child value",  write_key=CHILD_write_key )
    dump(execution_log)

    rdz.set( name = PARENT, value = "parent value", write_key=PARENT_write_key )
    rdz._subscribe( publisher = PARENT, subscriber = CHILD )
    rdz.set( name = PARENT, value = "parent changed value", write_key=PARENT_write_key )
    CHILD_mailbox = rdz.reserved["messages"]+CHILD
    message_to_child = rdz.client.hget( CHILD_mailbox, PARENT )
    assert message_to_child=="parent changed value"
