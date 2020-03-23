from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint


if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    for name in ['cop.json']:
        predictions = rdz.get(name="predictions::70::cop.json")
        print("---Predictions---")
        pprint.pprint([ (p,v) for p,v in predictions.items() if p<'00000001' ])



