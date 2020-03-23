from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from rediz.client import Rediz

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    rdz.client.flushall(asynchronous=True)