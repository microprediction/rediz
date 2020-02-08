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
    delay           = 1
    assert 1 in rdz.DELAYS
    assert 5 in rdz.DELAYS
    TARGET              = "target-db77f1c0d75f.json"
    SOURCE_write_key    = "source-key-01f339453-e057-4e98-9e26-eec6abee711f"
    TARGET_write_key    = "target-key-c73126a7df8339453-e057-4e98-9e26-eec6abee711f"
    assert rdz.is_valid_key(TARGET_write_key)
    assert rdz.is_valid_key(SOURCE_write_key)

    DELAY = rdz.delayed_name(name=SOURCE, delay=delay)
    rdz._delete_implementation(TARGET, SOURCE, DELAY)
    assert rdz.set(name=TARGET,write_key=TARGET_write_key,value=json.dumps({"temp":81}))   # Ensure existence
    assert rdz.set(name=SOURCE,write_key=SOURCE_write_key,value=json.dumps({"temp":77.6})) # Ensure existence
    assert rdz.exists(TARGET)
    assert rdz.exists(SOURCE)
    assert rdz.client.exists(*[SOURCE,TARGET])

    # Check that we can
    assert rdz._authorize(name=SOURCE, write_key=SOURCE_write_key)
    assert rdz.link( name=SOURCE,target=TARGET,delay=delay, write_key=SOURCE_write_key )  # Can create this before delay exists
    links = rdz.get_links(name=SOURCE,delay=delay)
    backlinks = rdz.get_backlinks(name=TARGET)
    assert TARGET in links
    assert rdz.delayed_name(name=SOURCE,delay=delay) in backlinks

    time.sleep(1.5)
    assert rdz.admin_promises()

    # By now delay::1 should exist

    assert rdz.client.exists(DELAY)
    rdz.set(name=SOURCE,write_key=SOURCE_write_key,value=json.dumps({"temp":79.6})) # Modify

    # TODO: Test unlink here


    # Deleting the source should remove the backlink from target->delay::n::source for all delays
    rdz.delete(name=SOURCE,write_key=SOURCE_write_key)
    backlinks = rdz.get_backlinks(name=TARGET )
    assert DELAY not in backlinks

    rdz.delete(name=TARGET,write_key=TARGET_write_key)
    assert not( rdz.client.exists(DELAY) ), "delete failed to clean up delay::"

