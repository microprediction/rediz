
from rediz.client import Rediz
import json, time
from rediz.rediz_test_config import REDIZ_TEST_CONFIG

EXACTABLE_FOX = REDIZ_TEST_CONFIG['EXACTABLE_FOX']

def test_repo():
    URL = 'https://github.com/microprediction/echochamber'
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    write_key = EXACTABLE_FOX
    rdz.set_repository(write_key=write_key, url=URL)
    url_back_1 = rdz.get_repository(rdz.shash(write_key))
    url_back_2 = rdz.get_repository(write_key)
    assert url_back_1==URL
    assert url_back_2==URL
    rdz.delete_repository(write_key=write_key)
    url_back_3 = rdz.get_repository(rdz.shash(write_key))
    assert url_back_3 is None

