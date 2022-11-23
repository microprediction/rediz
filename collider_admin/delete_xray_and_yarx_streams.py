
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from pprint import pprint


SURE = True


if __name__ == '__main__':
    rdz     = Rediz(**REDIZ_COLLIDER_CONFIG)
    ownership = rdz.client.hgetall(rdz._OWNERSHIP)
    names_to_delete = list()

    def matcher(name):
        return ('xray' in name) or ('yarx' in name)

    for name, _ in ownership.items():
        if matcher(name):
            names_to_delete.append(name)

    pprint(names_to_delete)

    if SURE:
        resultz = rdz._delete_implementation(names=names_to_delete)

