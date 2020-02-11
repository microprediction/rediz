from rediz.client import Rediz
import json
import time
import sys
from rediz.rediz_test_config import REDIZ_TEST_CONFIG
import numpy as np
# rm tmp*.json; pip install -e . ; python -m pytest tests/test_memory_usage_set.py ; cat tmp_memory_set.json

def dump(obj,name="tmp_memory_set.json"): # Debugging
    json.dump(obj,open(name,"w"))

def test_real():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    do_scalar(rdz)

def do_scalar(rdz):
    NAME      = 'NAME-64c-fe9.json'
    WRITE_KEY = "6d77759b-685a-4e25-b75b-6619bf1f1119"
    NUM       = 6
    rdz.client.flushall()
    rdz.delete(name=NAME,write_key=WRITE_KEY)
    raw_size = 4*NUM
    for _ in range(NUM):
        time.sleep(0.1)
        scalar_data = np.random.randn()
        sz = sys.getsizeof(scalar_data)
        assert rdz.is_scalar_value(scalar_data)
        assert rdz.is_small_value(scalar_data)
        assert rdz.set( name = NAME,  value = scalar_data,  write_key=WRITE_KEY ) is not None
        value_back = rdz.get( name= NAME )
        assert rdz.is_scalar_value( value_back )
        rdz.admin_promises()
        rdz.admin_garbage_collection()


    memory_report = rdz._size(NAME,with_report=True)
    total = memory_report["total"]
    memory_report.update({"raw_size":raw_size,"ratio":total/raw_size})
    rdz.delete(name=NAME, write_key=WRITE_KEY)

    for _ in range(50):
        rdz.admin_garbage_collection()
        time.sleep(0.1)

    dump(memory_report)

    memory_report_2 = rdz._size(NAME, with_report=True)
    dump(memory_report_2,"tmp_memory2.json")

    for _ in range(2):
        time.sleep(1)
        rdz.admin_garbage_collection()


def do_vector(rdz):
    NAME      = 'NAME-64c-fe9.json'
    WRITE_KEY = "6d77759b-685a-4e25-b75b-6619bf1f1119"
    NUM       = 5
    rdz.client.flushall()
    assert rdz.card() == 0

    DIM  = 20
    vector_data = list(np.random.randn(DIM))
    raw_size = 4*DIM*NUM
    for _ in range(NUM):
        vector_data = list(np.random.randn(DIM))
        sz = sys.getsizeof(vector_data)
        assert rdz.is_vector_value(vector_data)
        assert rdz.is_small_value(vector_data)
        time.sleep(0.1)
        assert rdz.set( name = NAME,  value = vector_data,  write_key=WRITE_KEY )
        value_back = rdz.get( name= NAME )
        assert rdz.is_vector_value( value_back )


    memory_report = rdz._size(NAME,with_report=True)
    total = memory_report["total"]
    memory_report.update({"raw_size":raw_size,"ratio":total/raw_size})
    rdz.delete(name=NAME, write_key=WRITE_KEY)


    slowlog = rdz.client.slowlog_get()
    dump(memory_report)
    dump(slowlog,"tmp_slowlog.json")
