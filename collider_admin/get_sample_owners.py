from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint


if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    for name in ['cop.json']:
        owners = rdz._get_sample_owners(name=name,delay=rdz.DELAYS[1])
        print("---Owners---")
        pprint.pprint(owners)




