
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, CELLOSE_BOBCAT
from pprint import pprint

log_name='_whatever_log'
ttl = 60
limit=50
data ={'bad gc-::':7}

if __name__ == '__main__':
    rdz     = Rediz(**REDIZ_COLLIDER_CONFIG)
    result  = rdz._log_to_list(log_name, ttl, limit, data=data)
    pprint(result)
