
from rediz.client import Rediz
from rediz.rediz_test_config import REDIZ_TEST_CONFIG

def flush():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    rdz.client.flushall()

if __name__=="__main__":
    flush()
