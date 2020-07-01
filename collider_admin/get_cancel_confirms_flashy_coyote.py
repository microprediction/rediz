from rediz.client import Rediz
from pprint import pprint
import json
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG,FLASHY_COYOTE


if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    confirms = rdz.get_confirms(write_key=FLASHY_COYOTE)
    for c in confirms:
        c_data = json.loads(c)
        if c_data.get('operation')=='cancel':
            pprint(c_data)