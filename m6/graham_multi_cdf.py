from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, AZOXAZOLE_BOA
from pprint import pprint

num_to_show = 5

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    import matplotlib.pyplot as plt
    NAME = 'ginj-intraday-tactical-asset-allocation-energy-mean.json'
    samples = rdz.get_predictions(name=NAME,delay=rdz.DELAYS[-1],write_key=AZOXAZOLE_BOA)
    raw = [ (ticket.split('::')[1],val) for ticket,val in samples.items() ]
    codes = list(set([c for c,v in raw]))
    for code in codes[:num_to_show]:
        animal = rdz.animal_from_code(code)
        smpl = [v for c,v in raw if c==code]
        plt.hist(smpl, bins=150, alpha=0.5, label=animal)
    plt.legend(loc='upper left')
    plt.title(NAME.replace('.json',''))
    plt.xlim(-0.2,0.2)
    plt.show()



