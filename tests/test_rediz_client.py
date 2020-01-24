from rediz.client import Rediz, default_is_valid_name, default_is_valid_key
from threezaconventions.crypto import random_key
import json, os, uuid

from rediz.rediz_test_config import REDIZ_TEST_CONFIG

def dump(obj,name="obj.json"):
    json.dump(obj,open("obj.json","w"))


def random_name():
    return random_key()+'.json'

def test_default_is_valid_key():
    s = str(uuid.uuid4())
    assert default_is_valid_key(s), "Thought "+s+" should be valid."
    s = "too short"
    assert default_is_valid_key(s)==False, "Thought "+s+" should be invalid"

def test_default_is_valid_name():
    s = 'dog-7214.json'
    assert default_is_valid_name(s), "oops"
    for s in ["25824ee3-d9bf-4923-9be7-19d6c2aafcee.json"]:
        assert default_is_valid_name(s),"Got it wrong for "+s


def test_coerce_inputs():
    names, values, write_keys = Rediz._coerce_inputs(name="dog",value=8,write_key="aslf",names=None, values=None, write_keys=None)
    assert names[0]=="dog"
    assert values[0]==8
    names, values, write_keys = Rediz._coerce_inputs(names=["dog","cat"],value=8,write_key="aslf",name=None, values=None, write_keys=None)
    assert names[0]=="dog"
    assert values[1]==8
    assert write_keys[1]=="aslf"
    names, values, write_keys = Rediz._coerce_inputs(names=["dog","cat"],value=8,write_keys=["aslf","blurt"],name=None, values=None, write_key=None)
    assert names[0]=="dog"
    assert values[1]==8
    assert write_keys[1]=="blurt"
    names, values, write_keys = Rediz._coerce_inputs(names=[None,None],value=8,write_keys=["aslf","blurt"],name=None, values=None, write_key=None)
    assert names[0] is None
    assert values[1]==8



def test__set():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    args = {"name": "3912eb73-f5e6-4f5e-9674-1a320779b7d9.json",
           "value": 25,
           "write_key": "db81045e-eead-44e0-b0a9-ba38d1d0395e"}
    res = rdz._set(**args)
    assert res["executed"][0]["value"]==25

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
    state = rdz.set(**state)
    assert rdz.get(**state)=="17"


def test_mixed():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    # Create two new records ... one rejected due to a poor key
    names      = [ None,          None,   random_name()     ]
    write_keys = [ random_key(),  None,   'too-short'       ]
    values     = [ json.dumps(8), "cat",   json.dumps("dog")]
    execution_log = rdz._set(names=names,write_keys=write_keys,values=values,verbose=True)
    assert len(execution_log["executed"])==2,"Expected 2 to be executed"
    assert len(execution_log["ignored"])==0,"Expected none ignored"
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
