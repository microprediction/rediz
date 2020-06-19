
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from pprint import pprint

STREAMS_TO_DELETE = ['space_mystery.json','bronx_traffic_absolute_speed.json','bronx_traffic_speed_on_change.json','verrazano_speed.json']

if __name__ == '__main__':
    rdz     = Rediz(**REDIZ_COLLIDER_CONFIG)
    result  = rdz._delete_implementation(names=STREAMS_TO_DELETE)
    pprint(result)
