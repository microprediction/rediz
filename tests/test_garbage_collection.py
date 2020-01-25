from rediz.client import Rediz, default_is_valid_name, default_is_valid_key
from threezaconventions.crypto import random_key
import json, os, uuid
from rediz.rediz_test_config import REDIZ_TEST_CONFIG


def dump(obj,name="obj.json"):
    json.dump(obj,open("obj.json","w"))

def _setup():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    access = rdz.set(value="42")
    rdz.delete(**access)

def test_delete():
    _setup()
