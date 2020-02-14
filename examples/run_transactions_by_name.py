from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    names = REDIZ_COLLIDER_CONFIG['names']

    all_keys = rdz.client.keys()
    all_trans = [ (k,rdz.client.ttl(k),rdz.client.memory_usage(k)) for k in all_keys if rdz.TRANSACTIONS in k ]

    pprint.pprint(all_trans[:5])
    if all_trans:
        example_trans = all_trans[0]
        trans = rdz.client.xrange(example_trans[0])
        pprint.pprint(trans)

        balances = rdz.client.hgetall(rdz._BALANCES)
        pprint.pprint(balances)