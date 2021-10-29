
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, CELLOSE_BOBCAT, OFFCAST_GOOSE, EMBLOSSOM_MOTH
from pprint import pprint

pattern = 'fred'

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    em = rdz.client.hgetall(rdz._EMAILS)
    pprint([ (code,email) for code,email in em.items() if pattern in email])



