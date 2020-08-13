import os
from sys import  platform
from getjson import getjson
from rediz.conventions import MICRO_CONVENTIONS_ARGS

# Load a couple of environment variables for local testing.
# These are secrets on github.
try:
    from rediz.rediz_test_config_private import NOTHING_MUCH
except:
    pass

test_config_url = os.getenv('TEST_CONFIG_URL')
test_config_failover_url = os.getenv('TEST_CONFIG_FAILOVER_URL')
REDIZ_TEST_CONFIG = getjson(url=test_config_url,failover_url=test_config_failover_url)
if REDIZ_TEST_CONFIG is None:
    raise Exception('Could not get configuration')

if platform=='darwin':
    REDIZ_TEST_CONFIG['DUMP']=True

REDIZ_FAKE_CONFIG = REDIZ_TEST_CONFIG['FAKE']
for arg in MICRO_CONVENTIONS_ARGS:
    if arg not in REDIZ_FAKE_CONFIG:
        raise Exception('Need to update REDIZ_FAKE_CONFIG to include '+arg)