# Get the monthly winners

from getjson import getjson
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, EMBLOSSOM_MOTH
from pprint import pprint

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    sponsor = rdz.shash(EMBLOSSOM_MOTH)
    prizes = getjson('https://api.microprediction.org/prizes/')
    print(rdz.get_monthly_sponsored_leaderboard(sponsor=sponsor))
    print(rdz.get_trivariate_monthly_sponsored_leaderboard(sponsor=sponsor))



