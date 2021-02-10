from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, MEETLE_CATTLE
import pprint

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    name = 'traffic-nj511-minutes-route_4_from_fort_lee_to_the_alexander_hamilton_bridge_via_the_upper_level.json'
    delay = 70
    leaderboards = dict()

    lb_names = [rdz.leaderboard_name(),
               rdz.leaderboard_name(name=name),
               rdz.leaderboard_name(name=None, delay=delay),
               rdz.leaderboard_name(name=name, delay=delay)]

    pprint.pprint(lb_names)