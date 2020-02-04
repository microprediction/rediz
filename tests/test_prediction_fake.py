from rediz.client import Rediz
import json, os, uuid, random, time
from rediz.rediz_test_config import REDIZ_TEST_CONFIG
import threading
import numpy as np
# rm tmp*.json; pip install -e . ; python -m pytest tests/test_prediction_fake.py ; cat tmp_prediction.json

def dump(obj,name="tmp_prediction.json"): # Debugging
    json.dump(obj,open(name,"w"))

FAKE_FEED = "fake-feed-7fb76d7c.json"

def test_fake_data_feed():
    rdz = Rediz()
    write_key = "6ab13c1c-b744-4d73-9fe9-5afaa3ecf427"
    values = np.cumsum(np.random.randn(100,1))
    for value in values:
        rdz.set(name=FAKE_FEED,write_key=write_key,value=0.1*value)
        time.sleep(0.05)
        rdz.admin_promises()

    rdz.delete(name=FAKE_FEED,write_key=write_key)
    balance = rdz.balance(write_key=write_key)
    dump({"balance":balance,"jackpot":rdz.jackpot()})

def dont_test_fake_prediction():
    # Set up sequence of events
    feed = threading.Thread(target=fake_data_feed)
    feed.run()

