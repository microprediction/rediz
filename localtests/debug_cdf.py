
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from pprint import pprint


def test_cdf():
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    cdf = rdz.get_cdf(name='die.json', delay=310, values=[-2.5,-1.5,-0.5,0.5,1.5,2.5])
    pprint(cdf)


#{'delay': 310, 'values': '-2.5,-1.5,-0.5,0.5,1.5,2.5'}