from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from pprint import pprint

# predictions::310::die.json

if __name__ == '__main__':
    rdz     = Rediz(**REDIZ_COLLIDER_CONFIG)
    promises = rdz.client.keys(pattern='*'+rdz._PREDICTIONS+'*')
    rdz.client.delete(*promises)
    promises = rdz.client.keys(pattern='*' + rdz._PROMISED + '*')
    rdz.client.delete(*promises)

    print('Deleted promises')