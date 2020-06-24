from rediz.rediz_test_config import REDIZ_TEST_CONFIG

def test_getthem():
    assert '887f5' in REDIZ_TEST_CONFIG['TESTING_KEYS'][0][0]