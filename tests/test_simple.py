import fakeredis
from rediz.rediz_test_config import REDIZ_TEST_CONFIG

def test_set_get():
    r = fakeredis.FakeStrictRedis(**REDIZ_TEST_CONFIG)
    r.set("foo","bar")
    assert "bar"==r.get('foo'),"the foo ain't bar"
