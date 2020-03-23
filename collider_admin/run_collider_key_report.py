from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint


def summarize(rdz,name,names):
    ttl = str( rdz.client.ttl(name) )
    in_keys = name in names
    memory = rdz.client.memory_usage(name)
    return "ttl="+ttl+" "+str(in_keys)+" mem="+str(memory)

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    all_names = rdz.client.smembers( rdz._NAMES )
    all_keys = rdz.client.keys()
    all_ttl = dict( [ (k,summarize(rdz,k,all_names)) for k in all_keys ] )
    pprint.pprint(all_ttl)





