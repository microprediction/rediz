from rediz.rediz_test_config import REDIZ_TEST_CONFIG
import json

def test_retrieval():
    assert isinstance(REDIZ_TEST_CONFIG,dict), json.dumps(REDIZ_TEST_CONFIG)
    assert 'num_predictions' in REDIZ_TEST_CONFIG
