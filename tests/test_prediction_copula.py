from rediz.client import Rediz
import numpy as np
import json, time, math
from rediz.rediz_test_config import REDIZ_TEST_CONFIG
CELLOSE_BOBCAT = REDIZ_TEST_CONFIG['CELLOSE_BOBCAT']


# rm tmp*.json; pip install -e . ; python -m pytest tests/test_prediction_copula.py ; cat tmp_prediction.json

def dump(obj,name="tmp_prediction_copula.json"): # Debugging
    if REDIZ_TEST_CONFIG["DUMP"]:
        json.dump(obj,open(name,"w"))

def feed(rdz,targets, write_key):
    values = [ 0.1*np.random.randn()*math.exp(np.random.randn()) for _ in range(3) ]
    budgets = [1.0 for _ in targets ]
    res = rdz.cset(names=targets,write_key=write_key,values=values,budgets=budgets)
    assert res, "Feed didn't work in test_prediction_copulas"
    time.sleep(0.5)
    rdz.mtouch(names=targets, write_key=write_key)


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
    set_res = rdz.set_scenarios(name=target, values=jiggered, write_key=write_key, delay=rdz.DELAYS[0])

def do_setup(rdz,targets):
    rdz._delete_implementation(names=targets)
    for target in targets:
        owners = rdz._get_sample_owners(name=target,delay=1)
        assert len(owners)==0

def tear_down(rdz,targets, target_key, model_key, model_key1, model_key2, model_key3, num_exec=0):
    for target in targets:
        samples       = rdz.get_samples(name=target, delay=1, write_key=target_key)
        lagged        = rdz.get_lagged(name=target)
        owners        = rdz.client.smembers(rdz._sample_owners_name(name=target,delay=1))
        predictions   = rdz.get_predictions(name=target, delay=1,write_key=target_key)
        cdf           = rdz.get_cdf(name=target,delay=1,values=[0.0, 1.0])
        links         = rdz._get_links_implementation(name=target, delay=1)
        backlinks     = rdz._get_backlinks_implementation(name=target)
        subscriptions = rdz._get_subscriptions_implementation(name=target)
        subscribers   = rdz._get_subscribers_implementation(name=target)
        confirms      = rdz.get_confirms(write_key=target_key)
        home          = rdz.get_home(write_key=target_key)


        if len(list(samples.values())):
            sample_std = np.nanstd(list(samples.values()))
            predictions_std = np.nanstd(list(predictions.values()))
        else:
            sample_std = 0.0
            predictions_std = 0.0

        report = {"promises_delivered":num_exec,
                  "performance":{"model":rdz.get_performance(write_key=model_key),
                              "model1": rdz.get_performance(write_key=model_key1),
                              "model2": rdz.get_performance(write_key=model_key2),
                              "model3": rdz.get_performance(write_key=model_key3),
                              "reserve":rdz.get_reserve()},
                  "leaderboards": dict([ (target+str(delay), rdz.get_leaderboard(name=target,delay=delay)) for delay in rdz.DELAYS ]),
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
                  "subscribers":subscribers,
                  "confirms":confirms,
                  "summary":rdz.get_summary(name=target)
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
    target_key = CELLOSE_BOBCAT
    model_key  = '191e30c156a97c9f83ffebcb473a4b83'      # Bestayed Fly
    model_key1 = 'dd98bd16e5f9f77e206a662285378206'      # Scytale Bass
    model_key2 = 'd4d06552e5a210e74000abf7fa25a989'      # Teemles Eel
    model_key3 = '427b90905ddbbf57c6f90e9178a05c33'      # Heatless Cod
    model_keys = [ model_key1, model_key2, model_key3, model_key]
    assert all( rdz.is_valid_key(key) for key in model_keys),"invalid key"
    targets    = ["fake-copula-1-7fb76d7c.json","fake-copula-2-7fb76d7c.json","fake-copula-3-7fb76d7c.json"]
    for ky in model_keys:
        rdz.delete_performance(write_key=ky)
    rdz.delete_performance(write_key=rdz._RESERVE)

    # Check that things are clean
    do_setup(rdz=rdz,targets=targets)

    # Data feed ...
    for _ in range(5):
        feed(rdz=rdz,targets=targets,write_key=target_key)
        time.sleep(0.25)

    # Start administering delays
    num_exec = 0
    for _ in range(6):
        time.sleep(0.5)
        num_exec += rdz.admin_promises()
        feed(rdz,targets,target_key)
        num_exec += rdz.admin_promises()
        for target in targets:
            model(rdz, target, model_key)
            model(rdz, target, model_key1)
        num_exec += rdz.admin_promises()

    # Should have promises executed by now...
    samples = rdz.get_samples(name=targets[0],delay=1,write_key=target_key)

    if False:
        import matplotlib.pyplot as plt
        plt.hist(list(samples.values()))
        plt.show()

    for _ in range(5*5):
        time.sleep(1)
        num_exec += rdz.admin_promises()
        feed(rdz, targets,  target_key)
        for target in targets:
            model(rdz, target, model_key)
            model(rdz, target, model_key1)
            model(rdz, target, model_key2)
            model(rdz, target, model_key3)
        samples = rdz.get_samples(name=target[0], delay=1,write_key=target_key)

    tear_down(rdz=rdz, targets=targets, target_key=target_key, model_key=model_key, model_key1=model_key1, model_key2=model_key2, model_key3=model_key3, num_exec=num_exec)

    for ky in model_keys:
        rdz.delete_performance(write_key=ky)


