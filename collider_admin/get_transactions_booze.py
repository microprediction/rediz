from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, BOOZE_LEECH, OOTHECA_MOTH, EMBLOSSOM_MOTH
import pprint

from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG


if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    NAME = 'c2_change_in_log_ethereum.json'
    delay = 70

    if False:
        rdz.set(name=NAME,value=0.1,write_key=EMBLOSSOM_MOTH)

    othe_trans = rdz.get_transactions(write_key=OOTHECA_MOTH,name=NAME,delay=delay)
    boo_trans = rdz.get_transactions(write_key=BOOZE_LEECH, name=NAME, delay=delay)

    pprint.pprint(othe_trans[-1])
    pprint.pprint(boo_trans[-1])
