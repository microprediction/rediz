from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from pprint import pprint

# predictions::310::die.json

if __name__ == '__main__':
    rdz     = Rediz(**REDIZ_COLLIDER_CONFIG)
    transactions = rdz.client.keys(pattern='*' + rdz.TRANSACTIONS + '*')
    rdz.client.delete(*transactions)
    print('Deleted transactions')