from rediz.client import Rediz
import pprint
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, CELLOSE_BOBCAT

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    pprint.pprint(rdz.get_home(write_key=CELLOSE_BOBCAT))
    print(CELLOSE_BOBCAT)