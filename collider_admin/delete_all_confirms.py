from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from pprint import pprint

# predictions::310::die.json

if __name__ == '__main__':
    rdz     = Rediz(**REDIZ_COLLIDER_CONFIG)
    confirms = rdz.client.keys(pattern='*' + rdz.CONFIRMS + '*')
    rdz.client.delete(*confirms)
    print('Deleted transactions')