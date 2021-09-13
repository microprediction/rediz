
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, CELLOSE_BOBCAT, OFFCAST_GOOSE, EMBLOSSOM_MOTH
from pprint import pprint

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)

    if __name__ == '__main__':
        winners = list()
        for write_key in [OFFCAST_GOOSE, EMBLOSSOM_MOTH]:
            lb = rdz.get_monthly_sponsored_leaderboard(sponsor=write_key)
            winners.append(next(iter(lb)))
        for write_key in [EMBLOSSOM_MOTH]:
            lb = rdz.get_bivariate_monthly_sponsored_leaderboard(sponsor=write_key)
            winners.append(next(iter(lb)))
            lb = rdz.get_trivariate_monthly_sponsored_leaderboard(sponsor=write_key)
            winners.append(next(iter(lb)))
        print(winners)



