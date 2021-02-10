# Get the monthly winners

from getjson import getjson
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, OFFCAST_GOOSE
from pprint import pprint

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    sponsor = rdz.shash(OFFCAST_GOOSE)
    prizes = getjson('https://api.microprediction.org/prizes/')
    lb = rdz.get_regular_monthly_sponsored_leaderboard(sponsor=sponsor)
    pprint(lb)



