from rediz.client import Rediz
import json, os, uuid, time

from rediz.rediz_test_config import REDIZ_TEST_CONFIG
# python -m pytest tests/test_links.py ; cat tmp_links.json

def dump(obj,name="tmp_links.json"):
    json.dump(obj,open(name,"w"))

def test_various_fake_and_real():
    rdz_fake = Rediz(decode_responses=True)
    rdz_real = Rediz(**REDIZ_TEST_CONFIG)
    for rdz in [rdz_fake,rdz_real]:
        do_test_link(rdz)

def do_test_link(rdz):
    SOURCE          = "ffa153b2-d0b0-4e6e-b0e8-b86bba1c9f88.json"
    DELAY           = "delay::1::"+SOURCE
    assert 5 in rdz.DELAY_SECONDS
    TARGET              = "39c01d69-db77-4f65-9d12-c7c9f1c0d75f.json"
    SOURCE_write_key    = "7ff8701f-87fb-4c24-8ea3-7e043166d220"
    TARGET_write_key    = "4127c731-3f31-4b26-ab97-5f51f926a7df"
    rdz._delete(TARGET,SOURCE, DELAY)
    assert rdz.set(name=TARGET,write_key=TARGET_write_key,value=json.dumps({"temp":81}))   # Ensure existence
    assert rdz.set(name=SOURCE,write_key=SOURCE_write_key,value=json.dumps({"temp":77.6})) # Ensure existence
    assert rdz.link( name=DELAY,target=TARGET,write_key=SOURCE_write_key )  # Can create this before delay exists (!)
    links = rdz.links( name=DELAY,write_key=SOURCE_write_key )
    backlinks = rdz.backlinks( name=TARGET,write_key=TARGET_write_key )
    assert TARGET in links
    assert DELAY in backlinks

    time.sleep(1.5)
    rdz.admin_promises()
    # By now delay::1 should exist
    assert rdz.exists(DELAY)
    rdz.set(name=SOURCE,write_key=SOURCE_write_key,value=json.dumps({"temp":79.6})) # Modify
    rdz._delete(SOURCE)
    backlinks = rdz._backlinks_implementation(TARGET)
    assert not backlinks

    rdz._delete(TARGET)
    assert not( rdz.exists(DELAY) ), "delete failed to clean up delay::"
