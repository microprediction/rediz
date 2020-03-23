from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint


if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    names = REDIZ_COLLIDER_CONFIG['names']
    reports = dict()
    for name in names:
        reports[name] = rdz._size(name=name,with_report=True)
    pprint.pprint(reports)




