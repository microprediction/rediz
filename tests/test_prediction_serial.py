from rediz.client import Rediz
import json, os, uuid, random, time
from rediz.rediz_test_config import REDIZ_TEST_CONFIG
import numpy as np
import math
# rm tmp*.json; pip install -e . ; python -m pytest tests/test_prediction_serial.py ; cat tmp_prediction.json

def dump(obj,name="tmp_prediction.json"): # Debugging
    json.dump(obj,open(name,"w"))

def feed(rdz,target, write_key):
    value = 0.1*np.random.randn()*math.exp(np.random.randn())
    rdz.set(name=target,write_key=write_key,value=value)

def model(rdz,target,write_key):
    ### Empirical distribution
    xs    = rdz.get_delayed(target,delays=rdz.DELAYS)
    xs1   = rdz.get_lagged_values(target)
    if all( x is None for x in xs1 ):
        jiggered = list(np.random.randn(rdz.NUM_PREDICTIONS))
    else:
        num_replicate = int(math.ceil( rdz.NUM_PREDICTIONS / len(xs1) ))
        x_samples = xs1*num_replicate
        x_samples = x_samples[:rdz.NUM_PREDICTIONS]
        noise     = np.random.randn(rdz.NUM_PREDICTIONS)
        jiggered  = [x+0.1*n for x,n in zip(x_samples,noise) ]
    rdz.predict(name=target,values=jiggered,write_key=write_key,delay=rdz.DELAYS[0])

def do_setup(rdz,target):
    rdz._delete_implementation(target)
    owners = rdz._get_sample_owners(name=target,delay=1)
    assert len(owners)==0

def tear_down(rdz,target, target_key, model_key, model_key1, model_key2, model_key3, num_exec=0) :
    samples       = rdz.get_samples(name=target, delay=1)
    lagged        = rdz.get_lagged(name=target)
    owners        = rdz.client.smembers(rdz._sample_owners_name(name=target,delay=1))
    predictions   = rdz.get_predictions(name=target, delay=1)
    links         = rdz._get_links_implementation(name=target, delay=1)
    backlinks     = rdz._get_backlinks_implementation(name=target)
    subscriptions = rdz._get_subscriptions_implementation(name=target)
    subscribers   = rdz._get_subscribers_implementation(name=target)

    if len(list(samples.values())):
        sample_std = np.nanstd(list(samples.values()))
        predictions_std = np.nanstd(list(predictions.values()))
    else:
        sample_std = 0.0
        predictions_std = 0.0

    report = {"promises_delivered":num_exec,
              "balances":{"owner":rdz.get_balance(write_key=target_key),
                          "model":rdz.get_balance(write_key=model_key),
                          "model1": rdz.get_balance(write_key=model_key1),
                          "model2": rdz.get_balance(write_key=model_key2),
                          "model3": rdz.get_balance(write_key=model_key3),
                          "reserve":rdz.get_reserve()},
              "errors":{"owner":rdz.get_errors(write_key=target_key),
                        "model":rdz.get_errors(write_key=model_key)},
              "samples":dict( list(samples.items())[:4] ),
              "owners":list(owners),
              "predictions":dict( list(predictions.items())[:4]),
              "sample_std":sample_std,
              "predictions_std": predictions_std,
              "links":links,
              "backlinks":backlinks,
              "subscriptions":subscriptions,
              "subscribers":subscribers
              }

    dump( report )
    rdz.delete(name=target, write_key=target_key)


def dont_test_serial_fake():
    rdz = Rediz()
    do_serial(rdz)

def test_serial_real():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    do_serial(rdz)

def do_serial( rdz ):
    target_key = "target-key-6ab13c1c-b744-4d73-9fe9-5afaa3ecf427"
    model_key  = "model-key-1e0ee756-001f-47e1-8724-898d239f7a46"
    model_key1 = "model1-key-1e0ee756-001f-47e1-8724-898d239f7a46"
    model_key2 = "model2-key-1e0ee756-001f-47e1-8724-898d239f7a46"
    model_key3 = "model3-key-1e0ee756-001f-47e1-8724-898d239f7a46"
    target     = "fake-feed-7fb76d7c.json"

    # Check that things are clean
    do_setup(rdz=rdz,target=target)

    # Data feed ...
    for _ in range(5):
        feed(rdz,target,target_key)
        time.sleep(0.25)

    # Start administering delays
    num_exec = 0
    for _ in range(6):
        time.sleep(0.5)
        num_exec += rdz.admin_promises()
        feed(rdz,target,target_key)
        num_exec += rdz.admin_promises()
        model(rdz,target, model_key)
        model(rdz, target, model_key1)
        num_exec += rdz.admin_promises()

    # Should have promises executed by now...
    samples = rdz.get_samples(name=target,delay=1)
    if False:
        import matplotlib.pyplot as plt
        plt.hist(list(samples.values()))
        plt.show()

    for _ in range(5*5):
        time.sleep(1)
        num_exec += rdz.admin_promises()
        feed(rdz, target,  target_key)
        model(rdz, target, model_key)
        model(rdz, target, model_key1)
        model(rdz, target, model_key2)
        model(rdz, target, model_key3)
        samples = rdz.get_samples(name=target, delay=1)

    tear_down(rdz, target, target_key, model_key, model_key1, model_key2, model_key3, num_exec)




