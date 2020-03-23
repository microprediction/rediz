from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from rediz.client import Rediz


rdz = Rediz(**REDIZ_COLLIDER_CONFIG)

names = REDIZ_COLLIDER_CONFIG['names']
budgets = [200 for _ in names ]
with_percentiles = True
with_copulas = True
values = [0.1, -0.2, 0.1, 0.3, 0.12]
write_keys = [ REDIZ_COLLIDER_CONFIG['write_key'] for _ in names ]
rdz.mset(names=names, values=values, budgets=budgets, write_keys=write_keys)
leaderboard = rdz.get_performance(name=names[0])
leaderboard = rdz.get_performance(name=names[0],delay=70)
#print(leaderboard)

cdf = rdz.get('cdf::70::cop.json')
#print(cdf)

delayed = rdz.get_delayed(name=names[0],delay=70)

summary = rdz.get_summary('cop.json')
print(summary)