from rediz.client import Rediz
import json
import time
import sys
from rediz.rediz_test_config import REDIZ_TEST_CONFIG
import numpy as np
# rm tmp*.json; pip install -e . ; python -m pytest tests/test_memory_scalar.py ; cat tmp_memory_scalar.json; cat tmp_error_log.json

def dump(obj,name="tmp_memory_scalar.json"): # Debugging
    json.dump(obj,open(name,"w"))

def test_real():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    rdz.client.flushall()
    time.sleep(0.15)
    do_scalar(rdz)

def do_scalar(rdz):
    NAME       = 'NAME-64c-fe9.json'
    WRITE_KEY  = "032d154c3feb97269d727e345e40b771"
    MODEL_KEYS = ["dad6936725fdf55be16fb1418db7b697","2653ae9f6f932b29d76263bbb20d6d76","f5f860baba93161e8bbb53b851d6f753"]
    PER_SECOND = 3
    NUM       = 5*PER_SECOND
    rdz.client.flushall()
    rdz.delete(name=NAME,write_key=WRITE_KEY)
    raw_size = 4*NUM
    for _ in range(NUM):
        time.sleep(1/PER_SECOND-0.05*len(MODEL_KEYS))
        scalar_data = np.random.randn()
        sz = sys.getsizeof(scalar_data)
        assert rdz.is_scalar_value(scalar_data)
        assert rdz.is_small_value(scalar_data)
        set_res =  rdz.set( name = NAME,  value = scalar_data,  write_key=WRITE_KEY, budget=1 )
        if set_res is None:
            exec_log = rdz.get_errors(write_key=WRITE_KEY)
            dump(exec_log,"tmp_error_log")
            set_res = rdz.set(name=NAME, value=scalar_data, write_key=WRITE_KEY, budget=1)
            assert set_res is not None
        value_back = rdz.get( name= NAME )
        assert rdz.is_scalar_value( value_back )
        rdz.admin_promises()
        rdz.admin_garbage_collection()
        for model_key in MODEL_KEYS:
            predict_values = list(np.random.randn(rdz.NUM_PREDICTIONS))
            time.sleep(0.05)
            rdz.set_scenarios(name=NAME, values=predict_values, write_key=model_key, delay=rdz.DELAYS[0])


    memory_report = rdz._size(NAME,with_report=True)
    total = memory_report["total"]
    memory_report.update({"raw_size":raw_size,"ratio":total/raw_size})
    rdz.delete(name=NAME, write_key=WRITE_KEY)

    for _ in range(1):
        rdz.admin_garbage_collection()
        time.sleep(0.1)

    dump(memory_report)

    keys = rdz.client.keys()
    dump(keys, "tmp_keys_before.json")

    for _ in range(1):
        time.sleep(0.15)
        rdz.admin_garbage_collection()

    keys = dict( [ (k,rdz.client.ttl(k)) for k in rdz.client.keys()] )
    dump(keys,"tmp_keys_after.json")