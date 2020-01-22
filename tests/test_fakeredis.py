import fakeredis

REDIS_TEST_CONFIG = {"decode_responses":True}  # Could supply a redis instance config here

def test_fakeredis_decode():
    r = fakeredis.FakeStrictRedis(**REDIS_TEST_CONFIG)
    r.set("foo","bar")
    assert "bar"==r.get('foo'),"the foo ain't bar"
