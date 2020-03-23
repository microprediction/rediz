from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint
import matplotlib.pyplot as plt
import numpy as np


if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    for name in REDIZ_COLLIDER_CONFIG["names"]:
        current = rdz.get(name=name)
        lagged = rdz.get_lagged_values(name=name)
        print("Current value is "+str(current))
        print("--- Lagged values ---")
        pprint.pprint(lagged)
        original = np.cumsum([0]+list(0.001*np.array(lagged)))
        plt.plot(original)
    plt.legend(REDIZ_COLLIDER_CONFIG["names"])
    plt.show()


