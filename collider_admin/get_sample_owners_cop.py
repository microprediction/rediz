from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint

from rediz.collider_config_private import BOOZE_MAMMAL

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    for name in ['cop.json']:
        delay = 910
        owners = rdz._get_sample_owners(name=name,delay=delay)
        print("---Owners---")
        pprint.pprint(owners)
        collective_predictions_name = rdz._predictions_name(name, delay)
        keys = [rdz._format_scenario(BOOZE_MAMMAL, k) for k in range(rdz.num_predictions)]

        samples_name = rdz._samples_name(name=name, delay=delay)
        samples = rdz.client.zrange(samples_name, start=0,end=-1)

        predict = rdz.client.zrange(collective_predictions_name, start=0, end=-1)
        print(predict)



