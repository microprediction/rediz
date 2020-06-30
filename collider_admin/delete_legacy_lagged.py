from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from pprint import pprint


PATTERNS = ['*lagged*z1~*310*',
            '*lagged*z1~*910*',
            '*lagged*z2~*310*',
            '*lagged*z2~*910*',
            '*lagged*z3~*310*',
            '*lagged*z3~*910*']


if __name__ == '__main__':
    rdz     = Rediz(**REDIZ_COLLIDER_CONFIG)
    for pattern in PATTERNS:
        lagged = rdz.client.keys(pattern=pattern)
        if lagged:
            rdz.client.delete(*lagged)
            print('Deleted lags for ' + pattern)