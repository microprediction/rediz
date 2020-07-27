
from rediz.client import Rediz
from rediz.rediz_test_config import REDIZ_TEST_CONFIG

EXACTABLE_FOX = REDIZ_TEST_CONFIG['EXACTABLE_FOX']

def test_repo():
    URL = 'https://github.com/microprediction/echochamber'
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    write_key = EXACTABLE_FOX
    rdz.set_repo(write_key=write_key, url=URL)
    url_back_1 = rdz.get_repo(rdz.shash(write_key))
    url_back_2 = rdz.get_repo(write_key)
    assert url_back_1==URL
    assert url_back_2==URL
    rdz.delete_repo(write_key=write_key)

