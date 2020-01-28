import fakeredis
from rediz.rediz_test_config import REDIZ_TEST_CONFIG


def test_fake():
    r = fakeredis.FakeStrictRedis(decode_responses=True)
    r.set("foo","bar")
    assert "bar"==r.get('foo'),"the foo ain't bar"
