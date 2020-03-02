from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint


if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    for name in ['cop.json']:

        #prctls = rdz.get_cdf(name=name)
        prctls = rdz.get('cdf::'+name)
        import matplotlib.pyplot as plt
        plt.plot(rdz.percentile_abscissa(),prctls)
        plt.title('CDF')
        plt.show()




