from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from rediz.redis_config import REDIZ_CONFIG
from rediz.client import Rediz
import time
import numpy as np
import random
from rediz.samplers import WeightedRandomGenerator

# An illustration of Rediz combining marginal and z-copula predictions from many different models

SYMBOLS          = REDIZ_COLLIDER_CONFIG["symbols"]
NAMES            = [ s+'.json' for s in SYMBOLS]
NUM_PARTICIPANTS = 10

def u_samples(rdz,name,method,decay):
    """ Weighted empirical jiggled bootstrap failing over to gaussian """
    lagged = rdz.get_lagged_values(name)
    if len(lagged) < 15 or method=='gaussian':
        return gu_samples(rdz=rdz,name=name,lagged=lagged)
    else:
        noise   = np.random.randn(rdz.NUM_PREDICTIONS)
        jiggle_noise = decay
        decays  = np.exp( [ -jiggle_noise*k for k in range(len(lagged)) ] )
        wrg     = WeightedRandomGenerator(weights=list(decays))
        ndxs = list()
        for _ in range(rdz.NUM_PREDICTIONS):
            ndxs.append( wrg() )
        return [ lagged[ndx]+eps*jiggle_noise for ndx,eps in zip(ndxs,noise) ]

def gu_samples(rdz, name, lagged=None):
    # Scenario generation for univariate time series
    lagged = lagged or rdz.get_lagged_values(name)
    if len(lagged) > 5:
        std_dev = np.nanstd(lagged)
        last_x  = lagged[-1]
    else:
        std_dev = 1.0
        last_x  = 0.0
    scenarios = [last_x + x * std_dev for x in list(np.random.randn(rdz.NUM_PREDICTIONS))]
    return scenarios

def z_samples(rdz,zname,method,decay):
    """ Scenario generation for z-embedded multivariate time series. """
    return u_samples(rdz=rdz, name=zname,method=method,decay=decay)

MODEL_COEFS   = [ 0.1*r/NUM_PARTICIPANTS for r in list(range(NUM_PARTICIPANTS)) ]
MODEL_METHODS = [ random.choice(['gaussian','empirical']) for _ in range(NUM_PARTICIPANTS) ]

def model(rdz):
    model_id  = random.choice(list(range(NUM_PARTICIPANTS)))
    model_coef = MODEL_COEFS[model_id]
    model_method = MODEL_METHODS[model_id]
    MODEL_write_key = str(model_id).zfill(3)+"-"+model_method+"-"+str(model_coef).zfill(2)+"-key-"
    delay = random.choice(rdz.DELAYS)

    target_type = random.choice(['name','derived'])

    if target_type=="name":
        name = random.choice(NAMES)
        scenarios = u_samples(name,method=model_method)
        rdz.predict(name=name,values=scenarios,write_key=MODEL_write_key,delay=delay, decay=model_coef)
    elif target_type=="derived":
        dim = random.choice([1,2,3])
        delay = random.choice(rdz.DELAYS)
        names = random.sample( NAMES, dim)
        zname = rdz.zcurve_name(names=names,delay=delay)
        zscenarios = z_samples(rdz=rdz,zname=zname,method=model_method, decay=model_coef)
        rdz.predict(name=zname, values=zscenarios, write_key=MODEL_write_key, delay=delay)
    return name, target_type


def model_loop():
    rdz = Rediz(**REDIZ_CONFIG)
    HOURS = 1
    PREDICTIONS_PER_SECOND = 50
    for _ in range(60 * 60 * HOURS * PREDICTIONS_PER_SECOND):
        before = time.time()
        target, prediction_type = model(rdz)
        after = time.time()
        print("Prediction type " + prediction_type + " for " + target + " took " + str(after - before) + " seconds.")
        wait_time = 1 / PREDICTIONS_PER_SECOND - (after - before)
        if wait_time > 0:
            time.sleep(wait_time)

if __name__ == '__main__':
    model_loop()


