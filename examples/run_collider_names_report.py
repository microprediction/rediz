from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint



if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    ownership = rdz.client.hgetall(rdz._OWNERSHIP)
    pprint.pprint(ownership)

    set_owners = rdz.client.smembers(rdz._NAMES)

    missing1 = [s for s in set_owners if not s in ownership.keys()]
    missing2 = [s for s in ownership.keys() if not s in set_owners]

    pprint.pprint({"missing1":missing1,"missing2":missing2})






