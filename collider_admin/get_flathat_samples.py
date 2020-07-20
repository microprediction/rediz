from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint

from rediz.collider_config_private import BOOZE_MAMMAL

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    entered_in = list()
    for name in ['bart_delays.json','hospital_bike_activity']:
        for delay in rdz.DELAYS:
            owners = rdz._get_sample_owners(name=name,delay=delay)
            animals = [ rdz.animal_from_key(key) for key in owners ]
            if any( 'Flathat' in animal for animal in animals):
                entered_in.append((name,delay))
    pprint.pprint(entered_in)




