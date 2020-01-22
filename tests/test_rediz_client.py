from rediz.client import Rediz, default_is_valid_name
from threezaconventions.crypto import random_key
import json
import os

def dump(obj,name="obj.json"):
    json.dump(obj,open("obj.json","w"))

REDIS_TEST_CONFIG = {"decode_responses":True}  # Could supply a redis instance config here

def random_name():
    return random_key()+'.json'

def test_default_is_valid_name():
    s = 'dog-7214.json'
    assert default_is_valid_name(s), "oops"
    for s in ["25824ee3-d9bf-4923-9be7-19d6c2aafcee.json"]:
        assert default_is_valid_name(s),"Got it wrong for "+s

def test_rediz_set_small_obscure():
    rdz = Rediz(**REDIS_TEST_CONFIG)
    names = [ None, None, random_name() ]
    write_keys = [ random_key(), None, None ]
    values = [ json.dumps(8), "cat", json.dumps("dog")]
    result = rdz.set(names=names,write_keys=write_keys,values=values)
    dump(result)

def test_rediz_set_large_obscure():
    rdz = Rediz(**REDIS_TEST_CONFIG)
    names = [ None, None, random_name() ]
    write_keys = [ random_key(), None, None ]
    values = [ json.dumps([7.6 for _ in range(1000)]), "cat", json.dumps("dog")]
    result = rdz.set(names=names,write_keys=write_keys,values=values)
