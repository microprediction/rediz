from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, EMBLOSSOM_MOTH
from pprint import pprint
import numpy as np

if __name__ == '__main__':
    try:
        import statsmodels.api as sm
    except ImportError:
        raise Exception('pip install statsmodels')
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    NAME = 'c5_ethereum.json'
    samples = rdz.get_predictions(name=NAME,delay=rdz.DELAYS[-1], write_key=EMBLOSSOM_MOTH)
    pprint(samples)
    print(len(samples))
    data = np.array(list(samples.values()))
    sm.qqplot(data, line='45',fit=True)
    import matplotlib.pyplot as plt
    plt.show()