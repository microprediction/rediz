
import time
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from rediz.client import Rediz

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    HOURS=10
    for k in range(60*60*2*HOURS):
        time.sleep(0.5)

        garbage_before = time.time()
        rdz.admin_garbage_collection()
        garbage_after = time.time()
        print("Garbage collection took " + str(garbage_after - garbage_before) + " seconds.")




