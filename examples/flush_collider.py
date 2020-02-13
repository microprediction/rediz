from rediz.redis_config import REDIZ_CONFIG
from rediz.client import Rediz

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_CONFIG)
    rdz.client.flushall(asynchronous=True)