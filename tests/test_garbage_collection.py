from rediz.client import Rediz, default_is_valid_name, default_is_valid_key
from threezaconventions.crypto import random_key
import json, os, uuid, random, time
from rediz.rediz_test_config import REDIZ_TEST_CONFIG



def dump(obj,name="garbage.json"):
    json.dump(obj,open("garbage.json","w"))



def setup_no_subs(rdz):
    access = rdz.set(value="42")
    name, write_key = access["name"], access["write_key"]
    rdz.client.expire(name=access["name"],time=0)
    import time
    time.sleep(0.1)
    return access

def test_delete_simple():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    access = rdz.set(value="42")
    name, write_key = access["name"], access["write_key"]
    assert rdz.get(**access)=="42"
    rdz._delete(names=[name])
    assert rdz.get(**access) is None

def test_expire():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    access = setup_no_subs(rdz)
    name, write_key = access["name"], access["write_key"]
    assert rdz.get(**access) is None
    assert rdz.client.sismember(name=rdz.reserved["names"],value=name)
    rdz._delete(names=[name])

def test_run_garbage_collection():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    rdz._garbage_collection()
    report = rdz.client.scard(rdz.reserved["names"])
    if False:
        dump(report)

def test_garbage_collection(num=100):
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    original_num = rdz.client.scard(rdz.reserved["names"])
    names = [ rdz.random_name() for _ in range(num) ]
    write_keys = [ rdz.random_key() for _ in range(num) ]
    value = "this is crud created by test_garbage_collection"
    access = rdz.set(names=names,write_keys=write_keys,value=value)
    expire_pipe = rdz.client.pipeline()
    for name in names:
        expire_pipe.expire(name=name,time=0)
    expire_pipe.execute()
    time.sleep(0.1)

    remaining = list()
    for iter_no in range(5):
        rdz._garbage_collection(max_searches=5, survey_fraction=0.01 )
        remaining.append( rdz.client.scard(rdz.reserved["names"]) )

    final_num = rdz.client.scard(rdz.reserved["names"])

    # Clean up scraps
    rdz._delete(*names)

def test_find_orphans_low_cardinality_test(num=20):

    rdz = Rediz(**REDIZ_TEST_CONFIG)

    original_num = rdz.client.scard(rdz.reserved["names"])
    if original_num<10000:
        # This test won't ultimately scale as it calls smembers
        original_set = rdz.client.smembers(rdz.reserved["names"])
        for k in [5,20,400]:
            some = rdz.client.srandmember(rdz.reserved["names"],k)
            some_unique = list(set(some))
            assert all( s in original_set for s in some )
            assert len(some_unique)<=original_num

        # Create some data with short ttl
        value  = "a string to store"
        names = [ rdz.random_name() for _ in range(num) ]
        write_keys = [ rdz.random_key() for _ in range(num) ]
        access = rdz.set(names=names,write_keys=write_keys,value=value)
        assert rdz.client.exists(*names)==len(names), "Names were not created as expected."
        for name in names:
            rdz.client.expire(name=name,time=5*60)

        expiring_names = [ n for n in names if random.choice(['expired','living'])=='expired' ]
        for expiring_name in expiring_names:
            rdz.client.expire(name=expiring_name,time=0)
        time.sleep(0.1)
        assert rdz.client.exists(*expiring_names)==0, "Names did not expire as expected"

        some_orphans = rdz._randomly_find_orphans(num=50)

        # Clean up most
        almost_all_orphans = rdz._randomly_find_orphans(num=10*num)
        if almost_all_orphans:
            rdz._delete(*almost_all_orphans)

        # Clean up scraps
        rdz._delete(*names)

        final_num = rdz.client.scard(rdz.reserved["names"])
        final_set = rdz.client.smembers(rdz.reserved["names"])
        set_diff_1  = final_set.difference(original_set)
        set_diff_2  = original_set.difference(final_set)

        if False:
            dump({"original_num":original_num,
                  "num_added":len(names),
                  "final_num":final_num,
                  "num_orphans":len(some_orphans),
                  "num_orphans_wider_search":len(almost_all_orphans),
                  "set_diff_1":list(set_diff_1),
                  "set_diff_2":list(set_diff_2)})
