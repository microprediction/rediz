from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from pprint import pprint
from pprint import pprint

PATTERNS = ['lagged_values::fwrd*','lagged_times::fwrd*']

SURE = True

if __name__ == '__main__':
    rdz     = Rediz(**REDIZ_COLLIDER_CONFIG)
    for pattern in PATTERNS:
        lagged = rdz.client.keys(pattern=pattern)
        if lagged:
            if SURE:
                rdz.client.delete(*lagged)
                print('Deleted lags for ' + pattern)
            else:
                pass
            pprint(lagged)