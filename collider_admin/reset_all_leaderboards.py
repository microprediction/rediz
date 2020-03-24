
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint

if __name__ == '__main__':
    rdz     = Rediz(**REDIZ_COLLIDER_CONFIG)
    streams = list(rdz.client.smembers(rdz._NAMES))
    rdz.client.delete(rdz.leaderboard_name(name=None))
    for name in streams:
        rdz.client.delete(rdz.leaderboard_name(name=name))
        for delay in rdz.DELAYS:
            rdz.client.delete(rdz.leaderboard_name(name=name,delay=delay))