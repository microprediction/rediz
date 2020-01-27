from rediz.client import Rediz
from threezaconventions.crypto import random_key
import json, os, uuid

from rediz.rediz_test_config import REDIZ_TEST_CONFIG

def dump(obj,name="helpers.json"):
    json.dump(obj,open("tmp_helpers.json","w"))


def random_name():
    return random_key()+'.json'

def test_assert_not_in_reserved():
    okay_examples = ["dog:prediction.json","cat:history.json"]
    has_bad_examples  = ["prediction::mine.json","okay.json"]
    Rediz.assert_not_in_reserved_namespace(okay_examples)
    try:
        Rediz.assert_not_in_reserved_namespace(has_bad_examples)
    except:
        return True
    assert False==True 

def test__is_valid_key():
    s = str(uuid.uuid4())
    assert Rediz.is_valid_key(s), "Thought "+s+" should be valid."
    s = "too short"
    assert Rediz.is_valid_key(s)==False, "Thought "+s+" should be invalid"

def test__is_valid_name():
    s = 'dog-7214.json'
    assert Rediz.is_valid_name(s), "oops"
    for s in ["25824ee3-d9bf-4923-9be7-19d6c2aafcee.json"]:
        assert Rediz.is_valid_name(s),"Got it wrong for "+s


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

def test_coerce_outputs():
    execution_log = {"executed":[ {"name":None,"ndx":1, "write_key":"123"},
                    {"name":"bill2","ndx":2, "write_key":None},
                    {"name":"sally0","ndx":0, "write_key":"12"} ]}
    out = Rediz._coerce_outputs(execution_log)
    dump(out)
