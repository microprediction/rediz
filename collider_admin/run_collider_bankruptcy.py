
import time
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from rediz.client import Rediz
import pprint

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    HOURS=10
    for k in range(60*60*2*HOURS):
        before = time.time()
        pprint.pprint( rdz.admin_bankruptcy() )
        after = time.time()
        print("Bankruptcy took " + str(after - before) + " seconds.")
        time.sleep(0.5)




