from rediz.client import Rediz
import json, os, uuid, random, time
from rediz.rediz_test_config import REDIZ_TEST_CONFIG
BELLEHOOD_BAT = REDIZ_TEST_CONFIG['BELLEHOOD_BAT']
TASTEABLE_BEE = REDIZ_TEST_CONFIG['TASTEABLE_BEE']
SHOOTABLE_CAT = REDIZ_TEST_CONFIG['SHOOTABLE_CAT']
BABLOH_CATTLE = REDIZ_TEST_CONFIG['BABLOH_CATTLE']



# rm tmp*.json; pip install -e . ; python -m pytest tests/test_subscription.py ; cat tmp_subscription.json
def dump(obj,name="tmp_subscription.json"): # Debugging
    if REDIZ_TEST_CONFIG["DUMP"]:
        json.dump(obj,open(name,"w"))

def don_test_subscription_singular():
    subscription_example(plural=False)

def dont_test_subscription_plural():
    subscription_example(plural=True)

def dont_test_plural_subscription_with_recall():
    subscription_example(plural=True,instant_recall=True)

def test_plural_subscription_without_recall():
    subscription_example(plural=True,instant_recall=False)

def subscription_example(plural=False,instant_recall=False):
    """ We subscribe first to one publisher and then to 50 at once, and
        verify propagation and cleanup after delete/unsubscribe
    """

    rdz = Rediz(instant_recall=instant_recall,**REDIZ_TEST_CONFIG)

    assert not rdz.get_subscriptions(name='non-existent-asdfaf.json')

    PUBLISHER             = 'PUBLISQHER_plural_'+str(plural)+'3b4e229a-ffb4-4fc2-8370-c147944aa2b.json'
    SUBSCRIBER            = 'SUBSCRIIBER_plural_'+str(plural)+'ed2b4f6-c6bd-464c-a9e9-322e0c3147.json'
    PUBLISHER_write_key   = BELLEHOOD_BAT if plural else TASTEABLE_BEE
    SUBSCRIBER_write_key  = SHOOTABLE_CAT if plural else BABLOH_CATTLE
    rdz._delete_implementation(PUBLISHER, SUBSCRIBER)

    assert rdz.set( name = SUBSCRIBER, value = "some value",       write_key=SUBSCRIBER_write_key )
    assert rdz.set( name = SUBSCRIBER, value = "some value",       write_key=SUBSCRIBER_write_key )
    assert rdz.set( name = PUBLISHER,  value = "some other value", write_key=PUBLISHER_write_key )
    if plural:
        rdz.msubscribe( sources = [PUBLISHER], name = SUBSCRIBER, write_key=SUBSCRIBER_write_key )
    else:
        rdz.subscribe( source = PUBLISHER, name = SUBSCRIBER, write_key=SUBSCRIBER_write_key )
    subscriptions = rdz.get_subscriptions(name=SUBSCRIBER )
    assert PUBLISHER in subscriptions
    subscribers = rdz.get_subscribers(name=PUBLISHER )
    assert SUBSCRIBER in subscribers

    # Check propagation
    assert rdz.set( name = PUBLISHER, value = "propagate this",    write_key=PUBLISHER_write_key ) # Should trigger propagation
    messages = rdz.messages( name=SUBSCRIBER, write_key=SUBSCRIBER_write_key )
    assert messages[PUBLISHER]=="propagate this"

    # Test removal
    rdz.unsubscribe( name=SUBSCRIBER, source=PUBLISHER, write_key=SUBSCRIBER_write_key)
    subscriptions = rdz.get_subscriptions(name=SUBSCRIBER )
    assert PUBLISHER not in subscriptions
    subscribers = rdz.get_subscribers(name=PUBLISHER )
    assert SUBSCRIBER not in subscribers

    # Test re-subscribe
    rdz.subscribe( source = PUBLISHER, name = SUBSCRIBER, write_key=SUBSCRIBER_write_key )

    # Check propagation
    assert rdz.set( name = PUBLISHER, value = "propagate this",    write_key=PUBLISHER_write_key ) # Should trigger propagation
    messages = rdz.messages( name=SUBSCRIBER, write_key=SUBSCRIBER_write_key )
    assert messages[PUBLISHER]=="propagate this"

    # Test removal with delete ...
    subscribers = rdz.get_subscribers(name=PUBLISHER)
    subscriptions = rdz.get_subscriptions(name=SUBSCRIBER)
    rdz.delete( name=SUBSCRIBER, write_key=SUBSCRIBER_write_key)
    subscriptions = rdz.get_subscriptions( name=SUBSCRIBER )
    subscribers = rdz.get_subscribers(name=PUBLISHER)
    assert not subscriptions
    assert SUBSCRIBER not in subscribers

    # Multiple sources
    publishers = dict()
    NUM_PUBLISHERS = 50
    for k in range(NUM_PUBLISHERS):
        source           = 'PUBLISHER_plural_'+ (str(plural).lower())+'-number_'+str(k)+'__3b4e944aa2b.json'
        write_key        = rdz.create_key(difficulty=6)
        publishers[source] = write_key
    sources    = list(publishers.keys())
    write_keys = list(publishers.values())
    values     = list(range(NUM_PUBLISHERS))

    assert rdz.set( name = SUBSCRIBER,
                   value = "I am back again",
               write_key = SUBSCRIBER_write_key ) # Should trigger propagation
    budgets = [3 for _ in sources]
    rdz._mset(names=sources, values=values, write_keys=write_keys, budgets=budgets)
    rdz._mset(names=sources, values=values, write_keys = write_keys, budgets=budgets)
    values_back = rdz.mget( names = sources )
    assert all( int(v1)==int(v2) for v1,v2 in zip(values, values_back))
    m_res =  rdz.msubscribe( name = SUBSCRIBER, sources = sources, write_key=SUBSCRIBER_write_key )
    assert m_res==len(sources)
    subscriptions = rdz.get_subscriptions(name=SUBSCRIBER )
    assert all( source in subscriptions for source in sources )
    for source, write_key in publishers.items():
        subscribers = rdz.get_subscribers(name=source )
        assert SUBSCRIBER in subscribers
        subscribers1 = rdz.get(rdz.SUBSCRIBERS+source)  # 'publisher_plural_true-number_0__3b4e944aa2b.json'
        assert SUBSCRIBER in subscribers1


    # Propagate ...
    changed_values  = [ int(2*v) for v in values ]
    budgets = [2 for v in values ]
    rdz._mset(names = sources, write_keys = write_keys, values=changed_values, budgets=budgets)
    messages = rdz.messages( name = SUBSCRIBER, write_key=SUBSCRIBER_write_key )
    for source, v in zip( sources, changed_values):
        assert messages[source]==str(v)

    # One more time with feeling ....
    changed_values  = [ int(3*v) for v in values ]
    rdz._mset(names = sources, write_keys = write_keys, values=changed_values, budgets=budgets)
    messages = rdz.messages( name = SUBSCRIBER, write_key=SUBSCRIBER_write_key )
    for source, v in zip( sources, changed_values):
        assert messages[source]==str(v)

    # Multiple delete of sources
    assert rdz.client.exists( *sources )==NUM_PUBLISHERS
    rdz.mdelete( names=sources, write_keys=write_keys )   # Expires but does not delete
    time.sleep(0.15)                                      # Redis checks every 0.1 seconds (probably)
    assert rdz.client.exists( *sources )<10, "Fail could be bad luck"         # Most will be deleted by now.

    for source, write_key in publishers.items():
        assert not rdz.get_subscribers(name=source )

    subscriptions = rdz.get_subscriptions(SUBSCRIBER)
    for source in sources:
        assert source not in subscriptions

    subscriptions = rdz.get_subscriptions(name=SUBSCRIBER )
    for source in sources:
        assert source not in subscriptions

    # Messages may persist or not depending on settings
    messages = rdz.messages( name = SUBSCRIBER, write_key= SUBSCRIBER_write_key )
    if rdz._INSTANT_RECALL:
        for source in sources:
            assert source not in messages
    else:
        assert len(messages)==NUM_PUBLISHERS

    rdz.delete(name=PUBLISHER,write_key=PUBLISHER_write_key)
    rdz.delete(name=SUBSCRIBER,write_key=SUBSCRIBER_write_key)



if __name__=="__main__":
    subscription_example(plural=False)
