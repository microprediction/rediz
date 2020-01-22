import threezaconventions
from threezaconventions import crypto
from threezaconventions.crypto import hash5, random_key, to_public

def test_conventions_import():
    assert len( hash5("lakjsdf") )>10

def test_keys():
    private_key = random_key()
    assert len(private_key)>10
    public_key  = to_public(private_key)
    assert public_key == hash5(hash5(private_key))
