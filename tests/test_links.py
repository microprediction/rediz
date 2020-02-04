from rediz.client import Rediz
import json, os, uuid, time

from rediz.rediz_test_config import REDIZ_TEST_CONFIG
# python -m pytest tests/test_links.py ; cat tmp_links.json

def dump(obj,name="tmp_links.json"):
    json.dump(obj,open(name,"w"))

def test_fake():
    rdz_fake = Rediz(delay_grace=60, delay_seconds=[1,5])
    do_test_link(rdz_fake)

def test_real():
    rdz_real = Rediz(delay_grace=900,**REDIZ_TEST_CONFIG)
    do_test_link(rdz_real)

def do_test_link(rdz):
    SOURCE          = "source-153f88.json"
    DELAY           = rdz.DELAYED+"1"+rdz.SEP+SOURCE
    assert 1 in rdz.DELAY_SECONDS
    assert 5 in rdz.DELAY_SECONDS
    TARGET              = "target-db77f1c0d75f.json"
    SOURCE_write_key    = "source-key-01f339453-e057-4e98-9e26-eec6abee711f"
    TARGET_write_key    = "target-key-c73126a7df8339453-e057-4e98-9e26-eec6abee711f"
    assert rdz.is_valid_key(TARGET_write_key)
    assert rdz.is_valid_key(SOURCE_write_key)
    rdz._delete(TARGET,SOURCE, DELAY)
    assert rdz.set(name=TARGET,write_key=TARGET_write_key,value=json.dumps({"temp":81}))   # Ensure existence
    assert rdz.set(name=SOURCE,write_key=SOURCE_write_key,value=json.dumps({"temp":77.6})) # Ensure existence
    assert rdz.exists(TARGET,SOURCE)==2

    # Check that we can
    assert rdz._authorize(name=SOURCE, write_key=SOURCE_write_key)
    assert rdz._authorize(name=DELAY, write_key=SOURCE_write_key)
    assert rdz.link( name=DELAY,target=TARGET,write_key=SOURCE_write_key )  # Can create this before delay exists
    links = rdz.links( name=DELAY,write_key=SOURCE_write_key )
    backlinks = rdz.backlinks( name=TARGET,write_key=TARGET_write_key )
    assert TARGET in links
    assert DELAY in backlinks

    time.sleep(1.5)
    assert rdz.admin_promises()

    # By now delay::1 should exist
    _exists = rdz.client.exists(DELAY)
    assert rdz.exists(DELAY)
    rdz.set(name=SOURCE,write_key=SOURCE_write_key,value=json.dumps({"temp":79.6})) # Modify

    # Deleting the source should remove the backlink from target->delay::n::source for all delays
    rdz.delete(name=SOURCE,write_key=SOURCE_write_key)
    backlinks = rdz.backlinks(name=TARGET,write_key=TARGET_write_key)
    assert DELAY not in backlinks

    rdz._delete(TARGET)
    assert not( rdz.exists(DELAY) ), "delete failed to clean up delay::"

