from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint


if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    for name in ['cop.json']:
        predictions = rdz.get_predictions(name=name,delay=rdz.DELAYS[0])
        print("---Predictions---")
        pprint.pprint([ (p,v) for p,v in predictions.items() ])



