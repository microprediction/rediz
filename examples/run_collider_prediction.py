from rediz.collider_config_private import COLLIDER_CONFIG
from rediz.redis_config import REDIZ_CONFIG
from rediz.client import Rediz
import time
import numpy as np
import random

SYMBOLS          = COLLIDER_CONFIG["symbols"]
NAMES            = [ s+'.json' for s in SYMBOLS]
NUM_PARTICIPANTS = 100

def model(rdz):
    delay     = rdz.DELAYS[0]
    scenarios = list(np.random.randn(rdz.NUM_PREDICTIONS))
    model_id  = random.choice(list(range(NUM_PARTICIPANTS)))
    MODEL_write_key = str(model_id)+"-model-outside-bd9-86-24-46da-99c8-0314af150298"
    for name in NAMES:
        rdz.predict(name=name,values=scenarios,write_key=MODEL_write_key,delay=delay)
    print("Model "+str(model_id)+" made predictions")

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_CONFIG)
    for _ in range(60*60):
        time.sleep(1)
        model(rdz)


