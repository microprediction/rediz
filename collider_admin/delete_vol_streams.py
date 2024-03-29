
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from pprint import pprint



if __name__ == '__main__':
    rdz     = Rediz(**REDIZ_COLLIDER_CONFIG)
    ownership = rdz.client.hgetall(rdz._OWNERSHIP)
    for name, write_key in ownership.items():
        if 'vlty_' in name:
            print('Del '+name)
            rdz._delete_implementation(name)

    PATTERNS = ['*lagged~*vlty*']

    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    for pattern in PATTERNS:
        lagged = rdz.client.keys(pattern=pattern)
        if lagged:
            rdz.client.delete(*lagged)
            print('Deleted lags for ' + pattern)




