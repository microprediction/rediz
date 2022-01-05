from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, EMBLOSSOM_MOTH, BOOZE_LEECH, OOTHECA_MOTH
from rediz.collider_config_private import FATHOM_GAZELLE as SPONSOR_WRITE_KEY
import pprint


if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    name = 'fathom_yy.json'
    booze_code = rdz.shash(BOOZE_LEECH)
    ooth_code = rdz.shash(OOTHECA_MOTH)
    samples = rdz.get_samples(name=name,delay=rdz.DELAYS[0],write_key=SPONSOR_WRITE_KEY)
    predictions =rdz.get_predictions(name=name,delay=rdz.DELAYS[0],write_key=SPONSOR_WRITE_KEY)
    print("---Samples---")
    ndx = '133'
    pprint.pprint([ (p,v) for p,v in samples.items() if ndx in p and (booze_code in p or ooth_code in p)])
    pprint.pprint([ (p,v) for p,v in predictions.items() if ndx in p and (booze_code in p or ooth_code in p)])




