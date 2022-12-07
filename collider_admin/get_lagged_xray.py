from rediz.client import Rediz
import pprint
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, CELLOSE_BOBCAT

# Used.  Datable Llama

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    rdz.set(name='three_body_x.json',value=3.85, write_key=CELLOSE_BOBCAT)
    pprint.pprint(len(rdz.get_lagged(name='quick_yarx_aapl.json')))