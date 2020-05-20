from rediz.client import Rediz
import pprint
from rediz.collider_config_private import OLD_REDIZ_COLLIDER_CONFIG
WRITE_KEY = OLD_REDIZ_COLLIDER_CONFIG["write_key"]

# Used.  Datable Llama

if __name__ == '__main__':
    rdz = Rediz(**OLD_REDIZ_COLLIDER_CONFIG)
    pprint.pprint(rdz.get_donations(with_key=True))