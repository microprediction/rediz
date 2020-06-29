


from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG,ALEMMAL_SLOTH,MALAXABLE_FOX
from pprint import pprint


if __name__ == '__main__':
    rdz     = Rediz(**REDIZ_COLLIDER_CONFIG)
    res = rdz._transfer_implementation(source_write_key=ALEMMAL_SLOTH, recipient_write_key=MALAXABLE_FOX, amount=500, as_record=True)
    pprint(res)