from rediz.client import Rediz
import json, time, math
from rediz.rediz_test_config import REDIZ_TEST_CONFIG
import numpy as np
from pprint import pprint
BELLEHOOD_BAT = REDIZ_TEST_CONFIG['BELLEHOOD_BAT']
TESTING_KEYS = REDIZ_TEST_CONFIG['TESTING_KEYS']

# rm tmp*.json; pip install -e . ; python -m pytest tests/test_prediction_serial.py ; cat tmp_prediction.json

def dump(obj,name="tmp_prediction.json"): # Debugging
    if REDIZ_TEST_CONFIG["DUMP"]:
        json.dump(obj,open(name,"w"))

def feed(rdz,target, write_key):
    value = 0.1*np.random.randn()*math.exp(np.random.randn())
    set_res = rdz.set(name=target,write_key=write_key,value=value)
    time.sleep(1)
    touch_res =rdz.touch(name=target, write_key=write_key)
    return 'percentiles' in set_res and touch_res


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
    return set_res

def do_setup(rdz,target):
    rdz._delete_implementation(target)
    owners = rdz._get_sample_owners(name=target,delay=1)
    assert len(owners)==0

def tear_down(rdz,target, target_key, model_key, model_key1, model_key2, model_key3, num_exec=0):

    target_code = rdz.shash(target_key)

    leaderboards = {'overall':rdz.get_leaderboard(),
                    'sponsor':rdz.get_monthly_sponsored_leaderboard(sponsor=target_code),
    'monthly_sponsored':rdz.get_monthly_sponsored_leaderboard(sponsor=target_code),
    'overall_leaderboard':rdz.get_monthly_overall_leaderboard(),
    'monthly_overall_leaderboard':rdz.get_previous_monthly_overall_leaderboard(),
    'previous_monthly_sponsored':rdz.get_previous_monthly_sponsored_leaderboard(sponsor=target_code),
    'monthly_bivariate_leaderboard':rdz.get_bivariate_monthly_sponsored_leaderboard(sponsor=target_code),
    'monthly_trivariate_leaderboard': rdz.get_trivariate_monthly_sponsored_leaderboard(sponsor=target_code),
    'monthly_regular_leaderboard': rdz.get_regular_monthly_sponsored_leaderboard(sponsor=target_code),
    'monthly_zscore_leaderboard': rdz.get_zscore_monthly_sponsored_leaderboard(sponsor=target_code)
                    }

    samples       = rdz.get_samples(name=target, delay=1,write_key=target_key)
    lagged        = rdz.get_lagged(name=target)
    owners        = rdz.client.smembers(rdz._sample_owners_name(name=target,delay=1))
    predictions   = rdz.get_predictions(name=target, delay=1, write_key=target_key)
    cdf           = rdz.get_cdf(name=target,delay=1,values=[0.0, 1.0])
    links         = rdz._get_links_implementation(name=target, delay=1)
    backlinks     = rdz._get_backlinks_implementation(name=target)
    subscriptions = rdz._get_subscriptions_implementation(name=target)
    subscribers   = rdz._get_subscribers_implementation(name=target)
    confirms      = rdz.get_confirms(write_key=target_key)
    volumes       = rdz.get_volumes()
    active        = rdz.get_active(write_key=model_key1)
    rdz.delete_all_scenarios(write_key=model_key1)
    rdz.delete_all_scenarios(write_key=model_key1)
    rdz.delete_all_scenarios(write_key=model_key1)
    bankruptcy_report = rdz.admin_bankruptcy(with_report=True)

    if len(list(samples.values())):
        sample_std = np.nanstd(list(samples.values()))
        predictions_std = np.nanstd(list(predictions.values()))
    else:
        sample_std = 0.0
        predictions_std = 0.0

    report = {"promises_delivered":num_exec,
              "balances":{"owner":rdz.get_performance(write_key=target_key),
                          "model":rdz.get_performance(write_key=model_key),
                          "model1": rdz.get_performance(write_key=model_key1),
                          "model2": rdz.get_performance(write_key=model_key2),
                          "model3": rdz.get_performance(write_key=model_key3),
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
              "subscribers":subscribers,
              "confirms":confirms,
              "leaderboards":leaderboards
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
    target_key = TESTING_KEYS[0][0]
    model_key  = TESTING_KEYS[1][0]
    model_key1 = TESTING_KEYS[2][0]
    model_key2 = TESTING_KEYS[3][0]
    model_key3 = TESTING_KEYS[4][0]
    target     = "test-pred-serial-x412.json"

    # Check that things are clean
    do_setup(rdz=rdz,target=target)

    # Data feed ...
    for _ in range(10):
        feed(rdz,target,target_key)
        time.sleep(0.25)

    # Start administering delays
    num_exec = 0
    for _ in range(6):
        time.sleep(0.5)
        num_exec += rdz.admin_promises()
        assert feed(rdz,target,target_key)
        num_exec += rdz.admin_promises()
        assert model(rdz,target, model_key)
        assert model(rdz, target, model_key1)
        assert model(rdz, target, model_key2)
        assert model(rdz, target, model_key3)
        num_exec += rdz.admin_promises()

    # Should have promises executed by now...
    samples = rdz.get_samples(name=target,delay=1,write_key=target_key)

    if False:
        import matplotlib.pyplot as plt
        plt.hist(list(samples.values()))
        plt.show()

    for _ in range(5*5):
        time.sleep(1)
        num_exec += rdz.admin_promises()
        assert feed(rdz, target,  target_key)
        assert model(rdz, target, model_key)
        assert model(rdz, target, model_key1)
        assert model(rdz, target, model_key2)
        assert model(rdz, target, model_key3)
        samples = rdz.get_samples(name=target, delay=1, write_key=target_key)

    tear_down(rdz, target, target_key, model_key, model_key1, model_key2, model_key3, num_exec)




