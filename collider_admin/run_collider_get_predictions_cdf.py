from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint


if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    name = 'c2_change_in_log_ethereum.json'
    delay = 70
    import matplotlib.pyplot as plt
    cdf = rdz.get_cdf(name=name,delay=delay)

    cdf_lagged = rdz.get_lagged_cdf(name=name)
    plt.plot(cdf['x'], cdf['y'], cdf_lagged['x'],cdf_lagged['y'])
    plt.legend(['predicted','empirical'])
    plt.grid()
    plt.show()








