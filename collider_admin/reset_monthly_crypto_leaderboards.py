# Get the monthly winners

from getjson import getjson
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, EMBLOSSOM_MOTH
from pprint import pprint

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    sponsor = rdz.shash(EMBLOSSOM_MOTH)
    write_key = EMBLOSSOM_MOTH
    prizes = getjson('https://api.microprediction.org/prizes/')
    lb = rdz.get_regular_monthly_sponsored_leaderboard(sponsor=sponsor)
    pprint(lb)
    rdz.delete_regular_monthly_sponsored_leaderboard(write_key=write_key)
    lb = rdz.get_regular_monthly_sponsored_leaderboard(sponsor=sponsor)
    pprint(lb)

    rdz.delete_bivariate_monthly_sponsored_leaderboard(write_key=EMBLOSSOM_MOTH)
    rdz.delete_trivariate_monthly_sponsored_leaderboard(write_key=EMBLOSSOM_MOTH)





