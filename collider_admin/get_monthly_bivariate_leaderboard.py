
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, EMBLOSSOM_MOTH
from pprint import pprint

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    pprint( rdz.get_bivariate_monthly_sponsored_leaderboard(sponsor=EMBLOSSOM_MOTH, readable=True) )
    print(EMBLOSSOM_MOTH)


