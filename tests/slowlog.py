
from rediz.client import Rediz
from rediz.rediz_test_config import REDIZ_TEST_CONFIG

def slowlog():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    rdz.client.slowlog_get()

if __name__=="__main__":
    log = slowlog()
    print(log)