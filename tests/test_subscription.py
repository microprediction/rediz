from rediz.client import Rediz
from threezaconventions.crypto import random_key
import json, os, uuid, random, time
from rediz.rediz_test_config import REDIZ_TEST_CONFIG


def dump(obj,name="tmp_subscription.json"): # Debugging
    json.dump(obj,open(name,"w"))


def test_subscription_singular():
    subscription_example(plural=False)

def test_subscription_plural():
    subscription_example(plural=True)

def subscription_example(plural=False):
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    PUBLISHER   = 'PUBLISHER_plural_'+str(plural)+'3b4e229a-ffb4-4fc2-8370-c147944aa2b.json'
    SUBSCRIBER  = 'SUBSCRIBER_plural_'+str(plural)+'ed2b4f6-c6bd-464c-a9e9-322e0c3147.json'
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
    assert rdz.set( name = PUBLISHER, value = "some new value",    write_key=PUBLISHER_write_key )
    SUBSCRIBER_mailbox    = rdz.MESSAGES+SUBSCRIBER
    message_to_SUBSCRIBER = rdz.client.hget( SUBSCRIBER_mailbox, PUBLISHER )
    assert message_to_SUBSCRIBER=="some new value"

    subscriptions = rdz.subscrptions(name=SUBSCRIBER,write_key=SUBSCRIBER_write_key)
    dump(subscriptions)

    rdz.delete(PUBLISHER)
    rdz.delete(SUBSCRIBER)
