from rediz.client import Rediz
from threezaconventions.crypto import random_key
import json, os, uuid

from rediz.rediz_test_config import REDIZ_TEST_CONFIG

def dump(obj,name="rediz.json"):
    json.dump(obj,open("tmp_rediz.json","w"))

def random_name():
    return random_key()+'.json'

def test_set_with_log():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    args = {"name": "3912eb73-f5e6-4f5e-9674-1a320779b7d9.json",
           "value": 25,
           "write_key": "db81045e-eead-44e0-b0a9-ba38d1d0395e"}
    res = rdz._set(**args)
    assert res["executed"][0]["value"]==25

    access = {"name": "3912eb73-f5e6-4f5e-9674-1a320779b7d9.json", "write_key": "db81045e-eead-44e0-b0a9-ba38d1d0395e", "value": 17}
    access = rdz.set(**access)
    assert "write_key" in access

def test_set():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    args = {"name": "3912eb73-f5e6-4f5e-9674-1a320779b7d9.json",
           "value": 25,
           "write_key": "db81045e-eead-44e0-b0a9-ba38d1d0395e"}
    res = rdz._set(**args)

def test_set_repeatedly():
    rdz   = Rediz(**REDIZ_TEST_CONFIG)
    state = {"name": "3912eb73-f5e6-4f5e-9674-1a320779b7d9.json",
             "write_key": "db81045e-eead-44e0-b0a9-ba38d1d0395e"}
    state.update({"value":17})
    dump(state)
    state = rdz.set(**state)
    assert rdz.get(**state)=="17"


def test_mixed():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    # Create two new records ... one rejected due to a poor key
    names      = [ None,          None,   random_name()     ]
    write_keys = [ random_key(),  None,   'too-short'       ]
    values     = [ json.dumps(8), "cat",   json.dumps("dog")]
    execution_log = rdz._set(names=names,write_keys=write_keys,values=values)
    assert len(execution_log["executed"])==2,"Expected 2 to be executed"
    assert len(execution_log["rejected"])==1,"Expected 1 rejection"
    assert execution_log["executed"][0]["ttl_days"]>0.25,"Expected ttl>0.25 days"
    assert sum( [ int(t["obscure"]==True) for t in execution_log["executed"] ])==2,"Expected 2 obscure"
    assert sum( [ int(t["new"]==True) for t in execution_log["executed"] ])==2,"Expected 2 new"


def test_mixed_log():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    names = [ None, None, random_name() ]
    write_keys = [ random_key(), None, random_key() ]
    values = [ json.dumps([7.6 for _ in range(1000)]), "cat", json.dumps("dog")]
    result = rdz._set(names=names,write_keys=write_keys,values=values)
