from rediz.client import Rediz
import json, os, uuid, time
from rediz.rediz_test_config_private import BELLEHOOD_BAT, TASTEABLE_BEE

from rediz.rediz_test_config import REDIZ_TEST_CONFIG
# pip install -e ; python -m pytest tests/test_links.py ; cat tmp_links.json

def dump(obj,name="tmp_links.json"):
    json.dump(obj,open(name,"w"))

def test_fake():
    rdz_fake = Rediz(delay_grace=60, delay_seconds=[1,5])
    do_test_link(rdz_fake)

def test_real():
    rdz_real = Rediz(delay_grace=900,**REDIZ_TEST_CONFIG)
    do_test_link(rdz_real)

def do_test_link(rdz):
    SOURCE          = "source7-153f88.json"
    delay           = 1
    assert 1 in rdz.DELAYS
    assert 5 in rdz.DELAYS
    TARGET              = "target7-db77f1c0d75f.json"
    SOURCE_write_key    = BELLEHOOD_BAT
    TARGET_write_key    = TASTEABLE_BEE
    assert rdz.is_valid_key(TARGET_write_key)
    assert rdz.is_valid_key(SOURCE_write_key)

    DELAY = rdz.delayed_name(name=SOURCE, delay=delay)
    rdz._delete_implementation(TARGET, SOURCE, DELAY)
    assert rdz.set(name=TARGET,write_key=TARGET_write_key,value=json.dumps({"temp":81}))  is not None # Ensure existence
    assert rdz.set(name=SOURCE,write_key=SOURCE_write_key,value=json.dumps({"temp":77.6}))  is not None # Ensure existence
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
    rdz.admin_promises()

    # By now delay::1 should exist

    assert rdz.client.exists(DELAY)
    rdz.set(name=SOURCE,write_key=SOURCE_write_key,value=json.dumps({"temp":79.6})) # Modify

    # TODO: Test unlink here


    # Deleting the source should remove the backlink from target->delay::n::source for all delays
    rdz.delete(name=SOURCE,write_key=SOURCE_write_key)
    backlinks = rdz.get_backlinks(name=TARGET )
    assert DELAY not in backlinks

    rdz.delete(name=TARGET,write_key=TARGET_write_key)
    time.sleep(0.15)  # Time for redis to find the expired name
    assert not( rdz.client.exists(DELAY) ), "delete failed to clean up delay::"

