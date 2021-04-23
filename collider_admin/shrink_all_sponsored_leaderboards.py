# Manually shrink leaderboards

from getjson import getjson
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, OFFCAST_GOOSE, EMBLOSSOM_MOTH
from pprint import pprint

WEIGHT = 0.5  # Start of month


if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    for write_key in [OFFCAST_GOOSE,EMBLOSSOM_MOTH]:
        rdz.multiply_regular_monthly_sponsored_leaderboard(write_key=write_key, weight=WEIGHT)
    for write_key in [EMBLOSSOM_MOTH]:
        rdz.multiply_bivariate_monthly_sponsored_leaderboard(write_key=write_key, weight=WEIGHT)
        rdz.multiply_trivariate_monthly_sponsored_leaderboard(write_key=write_key, weight=WEIGHT)




