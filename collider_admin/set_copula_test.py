from rediz.collider_config_private import HEBDOMAD_LEECH, BABLOH_CAMEL, MOBBABLE_FLEA, OBSOLETE_FLEA
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, EXACTABLE_FOX, DOODLE_MAMMAL
from rediz.client import Rediz
import numpy as np


TICKERS = ['xle', 'xlc', 'xly', 'xlp', 'xlf', 'xlv', 'xli', 'xlb', 'xlre', 'xlk', 'xlu']

if __name__=='__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    names = [ 'tmprdps_'+ticker+'.json' for ticker in TICKERS]
    is_rdps = len(names) >= 1 and (sum(['rdps_' in n.lower() for n in names]) > 3)
    print({'is_rdps':is_rdps})
    values = list(np.random.randn(11))
    res = rdz.mset(names=names, values=values, write_key=HEBDOMAD_LEECH, with_percentiles=True, with_copulas=True, budgets=[1 for _ in values])
    print(res)
    for name in names:
        values = sorted(np.random.randn(rdz.NUM_PREDICTIONS))
        rdz.set_scenarios(name=name, delay=rdz.DELAYS[-1], values=values, write_key=MOBBABLE_FLEA)
        rdz.set_scenarios(name=name, delay=rdz.DELAYS[-1], values=values, write_key=OBSOLETE_FLEA)
    print(HEBDOMAD_LEECH)




