from rediz.fakeout import fakeredis

def test_basic():
    r = fakeredis.FakeStrictRedis()
    r.set("foo","bar")
    assert "bar"==r.get('foo'),"the foo ain't bar"
