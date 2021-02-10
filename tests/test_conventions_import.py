from microconventions import shash
from rediz import Rediz
from rediz.rediz_test_config import REDIZ_TEST_CONFIG
import numpy as np


def test_conventions_import():
    assert len( shash('lakjsdf')) > 10


def test_conv():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    assert rdz.min_len > 6
    assert rdz.MIN_LEN > 7
    assert rdz.min_len==rdz.MIN_LEN
