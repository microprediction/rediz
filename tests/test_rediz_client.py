from rediz.client import Rediz
from threezaconventions.crypto import random_key
import json, os, uuid

from rediz.rediz_test_config import REDIZ_TEST_CONFIG

def dump(obj,name="tmp_rediz_client.json"):
    json.dump(obj,open(name,"w"))

def random_name():
    return random_key()+'.json'

def test_set_with_log():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    args = {"name": "3912eb73-f5e6-4f5e-9674-1a320779b7d9.json",
           "value": "25",
           "write_key": "db81045e-eead-44e0-b0a9-ba38d1d0395e"}
    rdz._delete(args["name"])  # Previous run
    res = rdz._pipelined_set(**args)
    dump(res)
    assert res["executed"][0]["value"]=="25"

    access = {"name": "3912eb73-f5e6-4f5e-9674-1a320779b7d9.json", "write_key": "db81045e-eead-44e0-b0a9-ba38d1d0395e", "value": 17}
    assert rdz.set(**access)==1
    rdz._delete(args["name"])

def test_pipelined_set():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    args = {"name": "3912eb73-f5e6-4f5e-9674-1a320779b7d9.json",
           "value": 25,
           "write_key": "db81045e-eead-44e0-b0a9-ba38d1d0395e"}
    res = rdz._pipelined_set(**args)

def test_set_repeatedly():
    rdz   = Rediz(**REDIZ_TEST_CONFIG)
    title = {"name": "3912eb73-f5e6-4f5e-9674-1a320779b7d9.json",
             "write_key": "db81045e-eead-44e0-b0a9-ba38d1d0395e"}
    assert rdz.set(value="17", **title)
    assert rdz.set(value="11", **title)
    assert rdz.set(value="14", **title)
    assert rdz.set(value="12", **title)
    assert rdz.set(value="11", **title)
    assert rdz.set(value="10", **title)
    assert rdz.get(title["name"])=="10"
    rdz.delete(**title)

def test_mixed():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    # Create two new records ... one rejected due to a poor key
    names      = [ None,          None,   random_name()     ]
    write_keys = [ random_key(),  None,   'too-short'       ]
    values     = [ json.dumps(8), "cat",   json.dumps("dog")]
    execution_log = rdz._pipelined_set(names=names,write_keys=write_keys,values=values)
    assert len(execution_log["executed"])==2,"Expected 2 to be executed"
    assert len(execution_log["rejected"])==1,"Expected 1 rejection"
    assert execution_log["executed"][0]["ttl"]>25,"Expected ttl>25 seconds"
    assert sum( [ int(t["obscure"]==True) for t in execution_log["executed"] ])==2,"Expected 2 obscure"
    assert sum( [ int(t["new"]==True) for t in execution_log["executed"] ])==2,"Expected 2 new"
    rdz._delete(names)

def test_mixed_log():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    names = [ None, None, random_name() ]
    write_keys = [ random_key(), None, random_key() ]
    values = [ json.dumps([7.6 for _ in range(1000)]), "cat", json.dumps("dog")]
    result = rdz._pipelined_set(names=names,write_keys=write_keys,values=values)
    rdz._delete(names)
