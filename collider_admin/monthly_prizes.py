# Get the monthly winners

from getjson import getjson
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    animal = rdz.animal_from_key('bdfd44affd28e6c5b45329d6d4df7729')
    prizes = getjson('https://devapi.microprediction.org/prizes/')
    winners = dict()
    for url, money in prizes.items():
        leaderboard = getjson(url)
        pass



