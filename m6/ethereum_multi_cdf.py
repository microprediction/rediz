from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, EMBLOSSOM_MOTH
from pprint import pprint

num_to_show = 3

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    import matplotlib.pyplot as plt
    NAME = 'c5_ethereum.json'
    samples = rdz.get_predictions(name=NAME,delay=rdz.DELAYS[-1],write_key=EMBLOSSOM_MOTH)
    raw = [ (ticket.split('::')[1],val) for ticket,val in samples.items() ]
    codes = list(set([c for c,v in raw]))
    for code in codes[:num_to_show]:
        animal = rdz.animal_from_code(code)
        smpl = [v for c,v in raw if c==code]
        plt.hist(smpl, bins=150, alpha=0.25, label=animal)
    plt.legend(loc='upper left')
    plt.xlim(-10,10)
    plt.show()



