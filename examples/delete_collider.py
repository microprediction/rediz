from rediz.collider_config_private import COLLIDER_CONFIG
from rediz.redis_config import REDIZ_CONFIG
from rediz.client import Rediz
import time

SYMBOLS = COLLIDER_CONFIG["symbols"]
NAMES   = [ s+'.json' for s in SYMBOLS]

def delete_collider(rdz):
    for name in NAMES:
        rdz.delete(name=name,write_key=COLLIDER_CONFIG["write_key"] )

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_CONFIG)
    delete_collider(rdz)
    time.sleep(1)
    rdz.admin_garbage_collection()