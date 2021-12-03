from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from rediz.client import Rediz
import time

SYMBOLS = REDIZ_COLLIDER_CONFIG["symbols"]
NAMES   = [ s+'.json' for s in SYMBOLS]

GOLF_SG_CATEGORIES = ['total','ott','app','arg','putt']


def delete_collider(rdz):
    for name in NAMES:
        rdz.delete(name=name,write_key=REDIZ_COLLIDER_CONFIG["write_key"] )

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    delete_collider(rdz)
    rdz.client.expire('z1~cop~70.json',1)
    time.sleep(1.1)
    rdz.admin_garbage_collection()