from rediz.client import Rediz
import json, os, uuid, time
from rediz.rediz_test_config_private import BELLEHOOD_BAT, TASTEABLE_BEE

# rm tmp*.json; pip install -e . ; python -m pytest tests/test_rediz_client.py ; cat tmp_rediz_client.json

from rediz.rediz_test_config import REDIZ_TEST_CONFIG



def dump(obj,name="tmp_rediz_client.json"):
    json.dump(obj,open(name,"w"))

def random_key():
	return str(uuid.uuid4())

def random_name():
    return random_key()+'.json'

def test_set_integer():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    title = {"name": "3912eb73-f5e6-4f5e-9674-1a320779b7d9.json","write_key": BELLEHOOD_BAT}
    rdz.delete(**title)  # Previous run
    res = rdz._pipelined_set(values=[25],names=[title["name"]],write_keys=[title["write_key"]], budgets=[1])
    dump(res)
    assert res["executed"][0]["value"]==25

    access = {"name": "3912eb73-f5e6-4f5e-9674-1a320779b7d9.json", "write_key": TASTEABLE_BEE, "value": 17}
    assert rdz.set(**access) is not None
    rdz._delete_implementation(access["name"])
    time.sleep(0.15)
    assert not rdz.exists(access["name"])

def test_set_repeatedly():
    rdz   = Rediz(**REDIZ_TEST_CONFIG)
    title = {"name": "3912eb73-f5e6-4f5e-9674-1a320779b7d9.json",
             "write_key": TASTEABLE_BEE}
    assert rdz.set(value="17", **title) is not None
    assert rdz.set(value="11", **title) is not None
    assert rdz.set(value="14", **title) is not None
    assert rdz.set(value="12", **title) is not None
    assert rdz.set(value="11", **title) is not None
    assert rdz.set(value="10", **title) is not None
    assert rdz.get(title["name"])=="10"
    rdz.delete(**title)

def test_mixed():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    # Create two new records ... one rejected due to a poor key
    names      = [ None,          None,   random_name()     ]
    write_keys = [ BELLEHOOD_BAT,  TASTEABLE_BEE,   'too-short'       ]
    values     = [ json.dumps(8), "cat",   json.dumps("dog")]
    budgets    = [  1,             10,     10000            ]
    execution_log = rdz._pipelined_set(names=names,write_keys=write_keys,values=values, budgets=budgets)
    assert len(execution_log["executed"])==2,"Expected 2 to be executed"
    assert len(execution_log["rejected"])==1,"Expected 1 rejection"
    assert execution_log["executed"][0]["ttl"]>25,"Expected ttl>25 seconds"
    assert sum( [ int(t["obscure"]==True) for t in execution_log["executed"] ])==2,"Expected 2 obscure"
    assert sum( [ int(t["new"]==True) for t in execution_log["executed"] ])==2,"Expected 2 new"
    rdz._delete_implementation(names)

def test_mixed_log():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    names = [ None, None, random_name() ]
    write_keys = [ random_key(), None, random_key() ]
    values = [ json.dumps([7.6 for _ in range(1000)]), "cat", json.dumps("dog")]
    budgets = [ 1 for _ in names ]
    result = rdz._pipelined_set(names=names,write_keys=write_keys,values=values, budgets=budgets)
    rdz._delete_implementation(names)
