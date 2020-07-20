from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint

from rediz.collider_config_private import BOOZE_MAMMAL

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    for name in ['bart_delays.json']:
        delay = 910
        owners = rdz._get_sample_owners(name=name,delay=delay)
        print("---Owners (public key)---")
        pprint.pprint(owners)
        animals = [ rdz.animal_from_key(key) for key in owners ]
        print("---Owners (animals)---")
        pprint.pprint(animals)

        print("---Predictions---")
        samples_name = rdz._samples_name(name=name, delay=delay)
        samples = rdz.client.zrange(samples_name, start=0, end=-1)
        pprint.pprint(samples)


