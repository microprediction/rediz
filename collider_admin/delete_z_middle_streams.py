
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from pprint import pprint



if __name__ == '__main__':
    rdz     = Rediz(**REDIZ_COLLIDER_CONFIG)
    ownership = rdz.client.hgetall(rdz._OWNERSHIP)
    for name, write_key in ownership.items():
        print(name)
        if 'z3~' in name and ('910' in name or '310' in name ):
            print('Del '+name)
            rdz._delete_implementation(name)




