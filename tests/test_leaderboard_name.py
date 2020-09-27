# make sure we are using old school version
from rediz.rediz_test_config import REDIZ_TEST_CONFIG
from rediz.client import Rediz


def test_leaderboard_name():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    rdz.leaderboard_name()