
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from pprint import pprint

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)

    pprint( rdz.get_monthly_leaderboard() )


