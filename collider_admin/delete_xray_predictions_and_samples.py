from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from pprint import pprint


if __name__ == '__main__':
    rdz     = Rediz(**REDIZ_COLLIDER_CONFIG)
    promises = rdz.client.keys(pattern='*'+rdz._PREDICTIONS+'*'+'xray*')
    rdz.client.delete(*promises)
    promises = rdz.client.keys(pattern='*' + rdz._PREDICTIONS + '*' + 'yarx*')
    rdz.client.delete(*promises)
    samples = rdz.client.keys(pattern='*' + rdz._SAMPLES + '*' + 'xray*')
    rdz.client.delete(*samples)
    samples = rdz.client.keys(pattern='*' + rdz._SAMPLES + '*' + 'yarx*')
    rdz.client.delete(*samples)
    print('Deleted samples')