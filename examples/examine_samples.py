from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint
import random
import numpy as np

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    names = REDIZ_COLLIDER_CONFIG['names']

    all_keys = rdz.client.keys()
    name = random.choice(names)
    delay = random.choice(rdz.DELAYS)


    samples = rdz.get_samples(name=name,delay=delay)
    values  = list(samples.values())
    summary = {"count": len(values),
               "mean":np.nanmean(values),
               "min":min(values),
               "max":max(values)}

    pprint.pprint(samples)
    pprint.pprint(summary)
    import matplotlib.pyplot as plt
    plt.hist(values)
    plt.title(name)
    plt.ylabel('Count')
    plt.xlabel('Scenario')
    plt.show()
