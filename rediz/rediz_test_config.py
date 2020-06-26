import os
from sys import  platform
from getjson import getjson

# Load a couple of environment variables for local testing.
# These are secrets on github.
try:
    from rediz.rediz_test_config_private import NOTHING_MUCH
except:
    pass

test_config_url = os.getenv('TEST_CONFIG_URL')
test_config_failover_url = os.getenv('TEST_CONFIG_FAILOVER_URL')
REDIZ_TEST_CONFIG = getjson(url=test_config_url,failover_url=test_config_failover_url)

if platform=='darwin':
    REDIZ_TEST_CONFIG['DUMP']=True
