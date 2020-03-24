
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    balances = rdz.client.hgetall(rdz._BALANCES)
    for write_key in balances.keys():
        rdz.delete_performance(write_key=write_key)