from muid import bhash, shash


def test_conventions_import():
    assert len( bhash(b'lakjsdf') )>10
    assert len( shash('lakjsdf')) > 10
    assert  bhash('dog'.encode('ascii'))==bhash('dog'.encode('utf-8'))

