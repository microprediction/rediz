
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, BELLBOY_CAMEL

# Hand of God

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    WRITE_KEY = BELLBOY_CAMEL
    print(rdz.client.hset(name=rdz._BALANCES, key=WRITE_KEY, value=-100000))
    print('Reset balance for ' + rdz.animal_from_key(WRITE_KEY))

