from rediz.client import Rediz
import pprint
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG

# Used.  Datable Llama

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    pprint.pprint(rdz.get_donations(with_key=True,len=13))