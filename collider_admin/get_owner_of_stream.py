from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint

name = 'electricity-fueltype-nyiso-wind.json'
name = 'electricity-load-nyiso-overall.json'

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    print(rdz._authority(name=name))
    print(rdz.animal_from_key(rdz._authority(name=name)))



