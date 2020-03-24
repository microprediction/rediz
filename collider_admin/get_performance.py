from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint

from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
WRITE_KEY = REDIZ_COLLIDER_CONFIG["write_key"]


if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    performance = rdz.get_performance(write_key=WRITE_KEY)
    pprint.pprint(performance)