
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from pprint import pprint


if __name__ == '__main__':
    rdz     = Rediz(**REDIZ_COLLIDER_CONFIG)
    ownership = rdz.client.hgetall(rdz._OWNERSHIP)
    for name, write_key in ownership.items():
        for delay in rdz.DELAYS:
            samples_name = rdz._samples_name(name=name, delay=delay)
            sample_owners_name = rdz._sample_owners_name(name=name,delay=delay)
            rdz.client.delete(samples_name)
            rdz.client.delete(sample_owners_name)
            print('Deleted samples and owners for '+samples_name)

    promises = rdz.client.keys(pattern='*promised*')
    rdz.client.delete(*promises)
    print('Deleted promises')




