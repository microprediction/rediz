from rediz.client import Rediz
from threezaconventions.crypto import random_key
import json, os, uuid

from rediz.rediz_test_config import REDIZ_TEST_CONFIG

def dump(obj,name="helpers.json"):
    json.dump(obj,open("tmp_helpers.json","w"))

def test__streams_support():
    rdz = Rediz(decode_responses=True)
    assert rdz._streams_support()==False, "Test failed because now fakeredis supports streams?!"

def random_name():
    return random_key()+'.json'

def test_card():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    assert rdz.card()>=0

def test_exists_delete():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    title = {"name":"d7ec2edb-d045-490e-acbd-7a05122d930e.json","write_key":"3e68a4e0-a827-4462-a714-676aa575802c"}
    name = title["name"]
    rdz._delete(name) # In case it is left over from previous
    assert rdz.exists(name)==0
    set_res = rdz._pipelined_set(value="10",budget=1,**title)
    exists_res = rdz.exists(name)
    #dump({"exists_res":exists_res,"set_res":set_res})
    assert exists_res==1
    delete_res = rdz.delete(**title)
    assert delete_res==1
    name = title["name"]
    assert rdz.exists(name)==0

def test_assert_not_in_reserved():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    okay_examples     = ["dog:prediction.json","cat:history.json"]
    has_bad_examples  = ["prediction::mine.json","okay.json"]
    rdz.assert_not_in_reserved_namespace(okay_examples)
    try:
        rdz.assert_not_in_reserved_namespace(has_bad_examples)
    except:
        return True
    assert False==True

def test__is_valid_key():
    s = str(uuid.uuid4())
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    assert rdz.is_valid_key(s), "Thought "+s+" should be valid."
    assert rdz.is_valid_key("too short")==False, "Thought "+s+" should be invalid"

def test__is_valid_name():
    s = 'dog-7214.json'
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    assert rdz.is_valid_name(s), "oops"
    for s in ["25824ee3-d9bf-4923-9be7-19d6c2aafcee.json"]:
        assert rdz.is_valid_name(s),"Got it wrong for "+s


def test_coerce_sources_plural():
    do_coerce_sources(plural=True,delays=[1])
    do_coerce_sources(plural=True,delays=[1,5])
    do_coerce_sources(plural=True,delay=1)

def do_coerce_sources(plural,delays):
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    source = None if plural else "me.json"
    sources = ["you.json"] if plural else None
    kwargs = {"source":source,"sources":sources,"delays":delays}
    dump({"kwargs":kwargs})
    augmented_sources = rdz._coerce_sources(**kwargs)

def test_coerce_inputs():
    names, values, write_keys = Rediz._coerce_inputs(name="dog",value="8",write_key="aslf",names=None, values=None, write_keys=None)
    assert names[0]=="dog"
    assert values[0]=="8"
    names, values, write_keys = Rediz._coerce_inputs(names=["dog","cat"],value="8",write_key="aslf",name=None, values=None, write_keys=None)
    assert names[0]=="dog"
    assert values[1]=="8"
    assert write_keys[1]=="aslf"
    names, values, write_keys = Rediz._coerce_inputs(names=["dog","cat"],value="12",write_keys=["aslf","blurt"],name=None, values=None, write_key=None)
    assert names[0]=="dog"
    assert values[1]=="12"
    assert write_keys[1]=="blurt"
    names, values, write_keys = Rediz._coerce_inputs(names=[None,None],value="me",write_keys=["aslf","blurt"],name=None, values=None, write_key=None)
    assert names[0] is None
    assert values[1]=="me"

def test_coerce_outputs():
    execution_log = {"executed":[ {"name":None,"ndx":1, "write_key":"123"},
                                    {"name":"bill2","ndx":2, "write_key":None},
                                    {"name":"sally0","ndx":0, "write_key":"12"}
                                ],
                    "rejected":[ {"name":None,"ndx":5, "write_key":None},
                                {"name":"bill17","ndx":6, "write_key":None},
                                {"name":"sally23","ndx":4, "write_key":None}
                                ]
                    }
    out = Rediz._coerce_outputs(execution_log)
