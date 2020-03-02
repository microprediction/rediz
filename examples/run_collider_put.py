from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from rediz.client import Rediz


rdz = Rediz(**REDIZ_COLLIDER_CONFIG)

names = REDIZ_COLLIDER_CONFIG['names']
budgets = [200 for _ in names ]
with_percentiles = True
with_copulas = True
values = [0.001, -0.002, 0.0011, 0.0003, 0.0012]
write_keys = [ REDIZ_COLLIDER_CONFIG['write_key'] for _ in names ]
rdz.mset(names=names, values=values, budgets=budgets, write_keys=write_keys)