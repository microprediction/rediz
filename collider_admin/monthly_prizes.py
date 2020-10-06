# Get the monthly winners

from getjson import getjson
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, OSTEAL_BEETLE
from pprint import pprint

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    sponsor = rdz.shash(OSTEAL_BEETLE)
    animal = rdz.animal_from_key(OSTEAL_BEETLE)
    prizes = getjson('https://api.microprediction.org/prizes/')
    lb = rdz.get_monthly_sponsored_leaderboard(sponsor=sponsor)
    pprint(lb)



