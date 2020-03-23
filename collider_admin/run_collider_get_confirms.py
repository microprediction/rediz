from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint


if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    confirms = rdz.get_confirms(write_key='0fb1e71565f99a0d3bb3f3c37857b00a')
    pprint.pprint(confirms)




