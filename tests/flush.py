
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG

def flush():
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    rdz.client.flushall()

if __name__=="__main__":
    flush()
