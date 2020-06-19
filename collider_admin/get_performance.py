from rediz.client import Rediz
import pprint
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, WRITE_KEY


if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    performance = rdz.get_performance(write_key=WRITE_KEY)
    pprint.pprint(performance)