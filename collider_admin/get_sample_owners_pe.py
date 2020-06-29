from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint

from rediz.collider_config_private import BOOZE_MAMMAL

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    for name in ['pe.json']:
        delay = 910
        owners = rdz._get_sample_owners(name=name,delay=delay)
        print("---Owners---")
        pprint.pprint(owners)



