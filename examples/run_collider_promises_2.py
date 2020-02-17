
import time
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from rediz.client import Rediz

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    HOURS=10
    for k in range(HOURS*60*60*2):
        time.sleep(0.5)
        garbage_before = time.time()
        rdz.admin_promises()
        garbage_after = time.time()
        print("Promise delivery took " + str(garbage_after - garbage_before) + " seconds.")




