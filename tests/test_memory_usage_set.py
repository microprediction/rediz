from rediz.client import Rediz
import json, os, uuid, random, time
from rediz.rediz_test_config import REDIZ_TEST_CONFIG
import numpy as np
# rm tmp*.json; pip install -e . ; python -m pytest tests/test_memory_usage_set.py ; cat tmp_memory_set.json

def dump(obj,name="tmp_memory_set.json"): # Debugging
    json.dump(obj,open(name,"w"))

def test_real():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    do_test(rdz)


def mysum(d):
    sum = 0
    vs = list(d.values())
    for v in vs:
        try:
            vf = float(v)
            sum += vf
        except:
            pass
    return sum

def do_test(rdz):
    NAME      = 'test-delay-c6bd-464c-asad-fe9.json'
    WRITE_KEY = "6d77759b-685a-4e25-b75b-6619bf1f1119"
    NUM       = 100
    for _ in range(NUM):
        vector_data = list(np.random.randn(50))
        import sys
        sz = sys.getsizeof(vector_data)
        assert rdz.is_vector_value(vector_data)
        assert rdz.is_small_value(vector_data)
        import time
        time.sleep(0.1)
        assert rdz.set( name = NAME,  value = vector_data,  write_key=WRITE_KEY )==1
        value_back = rdz.get( name= NAME )
        assert rdz.is_vector_value( value_back )

    derived = list(rdz.derived_names(NAME).values())
    mem_stats = dict(  [ ( derived_name, rdz.client.memory_usage(derived_name) ) for derived_name in derived ] )
    total = mysum( mem_stats )
    mem_stats.update({"total":total})
    mem_brief = dict( (k,v) for k,v in mem_stats.items() if isinstance(v,int))
    dump(mem_brief)