from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint

from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
WRITE_KEY = REDIZ_COLLIDER_CONFIG["write_key"]

WRITE_KEY = '74ab5a2c6205469402cb94d2935d3443'

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    performance = rdz.get_transactions(write_key=WRITE_KEY,name=None,delay=None)
    pprint.pprint(performance)