
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, STREAM_CREATORS

# Hand of God used to ensure testing streams don't go broke

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    for WRITE_KEY in STREAM_CREATORS:
        balance = rdz.client.hget(name=rdz._BALANCES, key=WRITE_KEY)
        if balance:
            print(rdz.client.hset(name=rdz._BALANCES, key=WRITE_KEY, value=10*1000*1000))
            print('Reset balance for ' + rdz.animal_from_key(WRITE_KEY))