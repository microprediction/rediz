
from rediz.client import Rediz
from rediz.rediz_test_config import REDIZ_TEST_CONFIG


def test_trash():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    rdz.admin_garbage_collection()

