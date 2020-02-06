from rediz.client import Rediz
import json, os, uuid, random, time
from rediz.rediz_test_config import REDIZ_TEST_CONFIG
import threading
import numpy as np
import math
# rm tmp*.json; pip install -e . ; python -m pytest tests/test_prediction_fake.py ; cat tmp_prediction.json

def dump(obj,name="tmp_prediction.json"): # Debugging
    json.dump(obj,open(name,"w"))

def feed(rdz,target, write_key):
    value = np.random.randn()*math.exp(np.random.randn())
    rdz.set(name=target,write_key=write_key,value=value)
    time.sleep(0.15)
    rdz.admin_promises()

def model(rdz,target,write_key):
    ### Empirical distribution
    xs    = rdz.get_delayed(target,delays=rdz.DELAY_SECONDS)
    xs1   = rdz.get_lagged(target)
    if all( x is None for x in xs1 ):
        jiggered = list(np.random.randn(rdz.NUM_PREDICTIONS))
    else:
        num_replicate = int(math.ceil( rdz.NUM_PREDICTIONS / len(xs1) ))
        x_samples = xs1*num_replicate
        x_samples = x_samples[:rdz.NUM_PREDICTIONS]
        noise     = np.random.randn(rdz.NUM_PREDICTIONS)
        jiggered  = [x+0.1*n for x,n in zip(x_samples,noise) ]
    assert rdz.predict(name=target,values=jiggered,write_key=write_key)

def tear_down(rdz,target, target_key, model_key):
    owner_balance = rdz.get_balance(write_key=target_key)
    model_balance = rdz.get_balance(write_key=model_key)
    dump({"owner":owner_balance,"model":model_balance,"jackpot":rdz.get_jackpot()})
    rdz.delete(name=target, write_key=target_key)


def test_fake():
    target_key = "target-key-6ab13c1c-b744-4d73-9fe9-5afaa3ecf427"
    model_key  = "model-key-1e0ee756-001f-47e1-8724-898d239f7a46"
    target     = "fake-feed-7fb76d7c.json"
    rdz = Rediz()
    for _ in range(5):
        feed(rdz,target,target_key)
        rdz.admin_promises()
    for _ in range(20):
        time.sleep(0.25)
        rdz.admin_promises()
        feed(rdz,target,target_key)
        rdz.admin_promises()
        model(rdz,target, model_key)
        rdz.admin_promises()
    # Should have promises executed by now
    samples = rdz.get_samples(name=target,delay=1)
    if False:
        import matplotlib.pyplot as plt
        plt.hist(list(samples.values()))
        plt.show()
    for _ in range(4*10):
        time.sleep(0.25)
        rdz.admin_promises()
        feed(rdz, target, target_key)
        model(rdz, target, model_key)

    tear_down(rdz, target, target_key, model_key)


def feed_loop(rdz,target,write_key):
    for _ in range(100):
        time.sleep(0.15)
        feed(rdz,target,write_key)

def model_loop(rdz,target,write_key):
    for _ in range(100):
        time.sleep(0.15)
        model(rdz,target,write_key)


def dont_test_real():
    target_key = "target-key-6ab13c1c-b744-4d73-9fe9-5afaa3ecf427"
    model_key  = "model-key-1e0ee756-001f-47e1-8724-898d239f7a46"
    target     = "real-feed-7fb76d7c.json"
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    rdz._delete(target)
    feed = threading.Thread(target=feed_loop, args=(rdz,target,target_key))
    feed.run()
    model = threading.Thread(target=model_loop, args=(rdz, target, model_key))
    feed.run()




