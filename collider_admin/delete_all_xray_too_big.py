from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from pprint import pprint

# predictions::310::die.json

if __name__ == '__main__':
    rdz     = Rediz(**REDIZ_COLLIDER_CONFIG)
    for i in range(16, 2000):
        pattern = '*xray_'+str(i)+'.*'
        kys = rdz.client.keys(pattern=pattern)
        if kys:
            print(i)
            rdz.client.delete(*kys)
