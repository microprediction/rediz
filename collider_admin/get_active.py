from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint
from rediz.collider_config_private import FLAMMABLE_COD


if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    pprint.pprint(rdz.get_active(write_key=FLAMMABLE_COD))




