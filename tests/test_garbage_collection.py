from rediz.client import Rediz
import json, random, time
from rediz.rediz_test_config import REDIZ_TEST_CONFIG
BELLEHOOD_BAT = REDIZ_TEST_CONFIG['BELLEHOOD_BAT']

# # rm tmp*.json; pip install -e . ; python -m pytest tests/test_garbage_collection.py ; cat tmp_garbage.json

def dump(obj,name="tmp_garbage.json"): # Debugging
    if REDIZ_TEST_CONFIG['DUMP']:
        json.dump(obj,open(name,"w"))

def test_delete_simple():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    name = rdz.random_name()
    write_key = BELLEHOOD_BAT
    title = {'name':name,'write_key':write_key}
    assert rdz.set(value="42",**title)
    dump(title)
    v = rdz.get(name)
    assert v=="42"
    rdz.delete(**title)
    time.sleep(1.1)
    assert rdz.get(name) is None

def test_expire():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    name = rdz.random_name()
    write_key = BELLEHOOD_BAT
    assert rdz.set(value="44",name=name,write_key=write_key)
    rdz.client.expire(name=name,time=0)
    import time
    time.sleep(0.1)
    assert rdz.get(name) is None
    assert rdz.client.sismember(name=rdz._NAMES, value=name)
    rdz._delete_implementation(names=[name])

def test_run_admin_garbage_collection():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    rdz.admin_garbage_collection()
    names = rdz._names()
    if names:
        report = rdz._size(name=names[0],with_report=True)
        dump(report)

def test_admin_garbage_collection(num=100):
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    original_num = rdz.card()
    names      = [ rdz.random_name() for _ in range(num) ]
    write_keys = [ BELLEHOOD_BAT for _ in names ]
    values = ["from test_admin_garbage_collection" for _ in write_keys ]
    budgets = [ 1 for _ in range(num) ]
    mset_res = rdz._mset(names=names, write_keys=write_keys, values=values, budgets=budgets)
    assert len(mset_res)==len(names)
    expire_pipe = rdz.client.pipeline()
    for name in names:
        expire_pipe.expire(name=name,time=0)
    expire_pipe.execute()
    time.sleep(0.15)

    remaining = list()
    for iter_no in range(5):
        rdz.admin_garbage_collection( fraction=0.01 )
        remaining.append( rdz.card() )

    final_num = rdz.card()
    rdz._delete_implementation(*names)

def test_find_orphans_low_cardinality_test(num=20):

    rdz = Rediz(**REDIZ_TEST_CONFIG)

    original_num = rdz.card()
    if original_num<10000:
        # This test won't ultimately scale as it calls smembers
        original_set = rdz.client.smembers(rdz._NAMES)
        for k in [5,20,400]:
            some = rdz.client.srandmember(rdz._NAMES, k)
            some_unique = list(set(some))
            assert all( s in original_set for s in some )
            assert len(some_unique)<=original_num

        # Create some data with short ttl
        names = [ rdz.random_name() for _ in range(num) ]
        write_key = BELLEHOOD_BAT
        value  = "a string to store"
        values = [value for _ in names ]
        budgets = [ 7 for _ in names ]
        title = rdz._mset(names=names, write_key=write_key, values=values, budgets=budgets)
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
            rdz._delete_implementation(*almost_all_orphans)

        # Clean up scraps
        rdz._delete_implementation(*names)

        final_num = rdz.card()
        final_set = rdz.client.smembers(rdz._NAMES)
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
