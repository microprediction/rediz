
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint

if __name__ == '__main__':
    rdz     = Rediz(**REDIZ_COLLIDER_CONFIG)

    streams = list(rdz.client.smembers(rdz._NAMES))
    rdz.client.delete(rdz.leaderboard_name(name=None))
    pipe = rdz.client.pipeline()
    for name in streams:
        if ('z2~' in name) or ('z3~' in name):
            rdz.client.delete(rdz.leaderboard_name(name=name))
            for delay in rdz.DELAYS:
                pipe.delete(rdz.leaderboard_name(name=name,delay=delay))
    exec = pipe.execute()
    print(sum(exec))