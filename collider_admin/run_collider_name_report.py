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
    names = REDIZ_COLLIDER_CONFIG['names']
    report = rdz._size(name=names[0],with_report=True)
    pprint.pprint(report)



