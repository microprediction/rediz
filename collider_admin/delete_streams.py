
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from pprint import pprint

STREAMS_TO_DELETE = ['5m_cardano.json','5m_ethereum.json','5m_ripple.json','5m_iota.json','ethereum_usd.json','ethereum_eur.json','bitcoin_usd.json','bitcoin_eur.json']

if __name__ == '__main__':
    rdz     = Rediz(**REDIZ_COLLIDER_CONFIG)
    result  = rdz._delete_implementation(names=STREAMS_TO_DELETE)
    pprint(result)
    resultz = rdz._delete_z1_implementation(names=STREAMS_TO_DELETE)
