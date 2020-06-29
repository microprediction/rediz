from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from pprint import pprint


if __name__ == '__main__':
    rdz     = Rediz(**REDIZ_COLLIDER_CONFIG)
    promises = rdz.client.keys(pattern='*promised*')
    rdz.client.delete(*promises)
    print('Deleted promises')