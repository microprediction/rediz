from rediz.client import Rediz, default_is_valid_name, default_is_valid_key
from threezaconventions.crypto import random_key
import json, os, uuid
from rediz.rediz_test_config import REDIZ_TEST_CONFIG


def dump(obj,name="obj.json"):
    json.dump(obj,open("obj.json","w"))

def test_delete_simple():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    access = rdz.set(value="42")
    assert rdz.get(**access)=="42"
    rdz.delete(**access)
    assert rdz.get(**access) is None

def setup_no_subs(rdz):
    access = rdz.set(value="42")
    name, write_key = access["name"], access["write_key"]
    rdz.client.expire(name=access["name"],time=1)
    import time
    time.sleep(1.5)
    return access

def test_expire():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    access = setup_no_subs(rdz)
    name, write_key = access["name"], access["write_key"]
    assert rdz.get(**access) is None
    assert rdz.client.sismember(name=rdz.reserved["names"],value=name)

def test_collect_no_subscriptions():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    access = setup_no_subs(rdz)
    name, write_key = access["name"], access["write_key"]
    rdz._delete(names=[name])
    assert rdz.get(**access) is None
    assert not( rdz.client.sismember(name=rdz.reserved["names"],value=name) )
