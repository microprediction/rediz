
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from pprint import pprint
from getjson import getjson

SURE = False


if __name__ == '__main__':
    rdz     = Rediz(**REDIZ_COLLIDER_CONFIG)
    ownership = rdz.client.hgetall(rdz._OWNERSHIP)
    names_to_delete = list()

    url = 'https://raw.githubusercontent.com/microprediction/microprediction/master/microprediction/live/xraytickers_discarded.json'
    DISCARDED = getjson(url, failover_url=url)

    def matcher(name):
        is_yarx = 'yarx_' in name

        if is_yarx:
            ticker = name.replace('yarx_').replace('.json', '')
            is_discarded = ticker in DISCARDED
            return is_discarded
        else:
            return False

    for name, _ in ownership.items():
        if matcher(name):
            names_to_delete.append(name)

    pprint(names_to_delete)

    if SURE:
        for name in names_to_delete:
            resultz = rdz._delete_implementation(names=names_to_delete)

