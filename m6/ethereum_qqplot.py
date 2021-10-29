from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, EMBLOSSOM_MOTH
from pprint import pprint

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    NAME = 'c5_ethereum.json'
    samples = rdz.get_predictions(name=NAME,delay=rdz.DELAYS[-1], write_key=EMBLOSSOM_MOTH)
    pprint(samples)
    print(len(samples))
    import statsmodels.api as sm
    sm.qqplot(test, line='45')