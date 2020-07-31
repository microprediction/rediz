# Get the monthly winners

from getjson import getjson
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    prizes = getjson('https://devapi.microprediction.org/prizes/')
    winners = dict()
    for url, money in prizes.items():
        leaderboard = getjson(url)
        pass



