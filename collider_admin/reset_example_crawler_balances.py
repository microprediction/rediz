
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, EXAMPLE_CRAWLERS

# Hand of God used to ensure testing streams don't go broke

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    for WRITE_KEY in EXAMPLE_CRAWLERS:
        balance = rdz.client.hget(name=rdz._BALANCES, key=WRITE_KEY)
        if balance and float(balance)<100000:
            print(rdz.client.hset(name=rdz._BALANCES, key=WRITE_KEY, value=1000000))
            print('Reset balance for ' + rdz.animal_from_key(WRITE_KEY))