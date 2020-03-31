from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint
import time

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)

    start_time = time.time()
    NAMES = list(rdz.client.smembers(rdz._NAMES))
    for delay in rdz.DELAYS:
        cdfs = dict()
        for name in NAMES:
            cdfs[name] = rdz.get_cdf(name=name,delay=rdz.delays[0],top=3, min_balance=20)

    end_time = time.time()
    print("Got all "+str(len(cdfs))+" in "+str(end_time-start_time))