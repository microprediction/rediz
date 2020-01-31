from rediz.client import Rediz
from threezaconventions.crypto import random_key
import json, os, uuid, random, time
from rediz.rediz_test_config import REDIZ_TEST_CONFIG

# rm tmp*.json; pip install -e . ; python -m pytest tests/test_subscription.py ; cat tmp_subscription.json
def dump(obj,name="tmp_subscription.json"): # Debugging
    json.dump(obj,open(name,"w"))

def test_subscription_singular():
    subscription_example(plural=False)

def dont_test_subscription_plural():
    subscription_example(plural=True)

def subscription_example(plural=False):
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    PUBLISHER             = 'PUBLISHER_plural_'+str(plural)+'3b4e229a-ffb4-4fc2-8370-c147944aa2b.json'
    SUBSCRIBER            = 'SUBSCRIBER_plural_'+str(plural)+'ed2b4f6-c6bd-464c-a9e9-322e0c3147.json'
    PUBLISHER_write_key   = "b0b5753b-14e6-4051-b13e-132bb13ed1a9_plural="+str(plural)
    SUBSCRIBER_write_key  = "caa09e4a-3901-4cdf-8301-774184e584f3_plural="+str(plural)
    rdz._delete(PUBLISHER,SUBSCRIBER)

    assert rdz.set( name = SUBSCRIBER, value = "some value",       write_key=SUBSCRIBER_write_key )
    assert rdz.set( name = SUBSCRIBER, value = "some value",       write_key=SUBSCRIBER_write_key )
    assert rdz.set( name = PUBLISHER,  value = "some other value", write_key=PUBLISHER_write_key )
    if plural:
        rdz.msubscribe( sources = [PUBLISHER], name = SUBSCRIBER, write_key=SUBSCRIBER_write_key )
    else:
        rdz.subscribe( source = PUBLISHER, name = SUBSCRIBER, write_key=SUBSCRIBER_write_key )
    subscriptions = rdz.subscriptions(name=SUBSCRIBER,write_key=SUBSCRIBER_write_key)
    assert PUBLISHER in subscriptions
    subscribers = rdz.subscribers(name=PUBLISHER,write_key=PUBLISHER_write_key)
    assert SUBSCRIBER in subscribers

    # Check propagation
    assert rdz.set( name = PUBLISHER, value = "propagate this",    write_key=PUBLISHER_write_key ) # Should trigger propagation
    messages = rdz.messages( name=SUBSCRIBER, write_key=SUBSCRIBER_write_key )
    assert messages[PUBLISHER]=="propagate this"

    # Test removal
    rdz.unsubscribe( name=SUBSCRIBER, source=PUBLISHER, write_key=SUBSCRIBER_write_key)
    subscriptions = rdz.subscriptions(name=SUBSCRIBER,write_key=SUBSCRIBER_write_key)
    assert PUBLISHER not in subscriptions
    subscribers = rdz.subscribers(name=PUBLISHER,write_key=PUBLISHER_write_key)
    assert SUBSCRIBER not in subscribers

    # Test re-subscribe
    rdz.subscribe( source = PUBLISHER, name = SUBSCRIBER, write_key=SUBSCRIBER_write_key )

    # Check propagation
    assert rdz.set( name = PUBLISHER, value = "propagate this",    write_key=PUBLISHER_write_key ) # Should trigger propagation
    messages = rdz.messages( name=SUBSCRIBER, write_key=SUBSCRIBER_write_key )
    assert messages[PUBLISHER]=="propagate this"

    # Test removal with delete ...
    rdz.delete( name=SUBSCRIBER, write_key=SUBSCRIBER_write_key)
    subscriptions = rdz.subscriptions(name=SUBSCRIBER,write_key=SUBSCRIBER_write_key)
    assert subscriptions is None
    subscribers = rdz.subscribers(name=PUBLISHER,write_key=PUBLISHER_write_key)
    assert SUBSCRIBER not in subscribers

    # Multiple sources
    publishers = dict()
    NUM = 50
    for k in range(NUM):
        source           = 'PUBLISHER_plural_'+str(plural)+'-number_'+str(k)+'__3b4e944aa2b.json'
        write_key        = 'PUBLISHER_plural_'+str(plural)+'--'+str(k)+'3b4e944aa2b_KEY'
        publishers[source] = write_key
    sources    = list(publishers.keys())
    write_keys = list(publishers.values())
    values     = list(range(NUM))

    assert rdz.set( name = SUBSCRIBER,
                   value = "I am back again",
               write_key = SUBSCRIBER_write_key ) # Should trigger propagation

    rdz.mset(names=sources,values=values, write_keys=write_keys)
    assert rdz.mset( names = sources,  write_keys = write_keys, values=values )==NUM
    values_back = rdz.mget( names = sources )
    assert all( int(v1)==int(v2) for v1,v2 in zip(values, values_back))
    assert rdz.msubscribe( name = SUBSCRIBER, sources = sources, write_key=SUBSCRIBER_write_key )
    subscriptions = rdz.subscriptions(name=SUBSCRIBER,write_key=SUBSCRIBER_write_key)
    assert all( source in subscriptions for source in sources )
    for source, write_key in publishers.items():
        subscribers = rdz.subscribers( name=source, write_key=write_key )
        assert SUBSCRIBER in subscribers

    # Propagate ...
    changed_values  = [ int(2*v) for v in values ]
    rdz.mset( names = sources,  write_keys = write_keys, values=changed_values )
    messages = rdz.messages( name = SUBSCRIBER, write_key=SUBSCRIBER_write_key )
    for source, v in zip( sources, changed_values):
        assert messages[source]==str(v)

    # One more time with feeling ....
    changed_values  = [ int(3*v) for v in values ]
    rdz.mset( names = sources,  write_keys = write_keys, values=changed_values )
    messages = rdz.messages( name = SUBSCRIBER, write_key=SUBSCRIBER_write_key )
    for source, v in zip( sources, changed_values):
        assert messages[source]==str(v)


    rdz._delete(PUBLISHER)
    rdz._delete(SUBSCRIBER)


if __name__=="__main__":
    subscription_example(plural=False)
