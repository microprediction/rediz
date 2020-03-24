from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)

    LEADERBOARDS = [None, 'bronx_traffic_speed_on_change.json','three_body_x.json','cop.json','z3~three_body_x~three_body_y~three_body_z~10810.json','z2~three_body_x~three_body_y~910.json']

    leaderboards = dict()
    for name in LEADERBOARDS:
        leaderboards[name] = rdz.get_leaderboard(name=name)

    pprint.pprint(leaderboards)