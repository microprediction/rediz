from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)

    NAMES = ['c5_bitcoin.json']

    cdfs = dict()
    for name in NAMES:
        cdfs[name] = rdz.get_cdf(name=name,delay=rdz.DELAYS[0],top=3, min_balance=20)
