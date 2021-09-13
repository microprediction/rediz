from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint

from rediz.collider_config_private import BOOZE_MAMMAL

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    for name in ['emojitracker-twitter-heavy_black_heart.json']:
        delay = 910
        samples = rdz.get_samples(name=name,delay=delay)
        print("---Samples---")
        pprint.pprint(samples)



