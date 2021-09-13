
from rediz.client import Rediz
import json, time
from rediz.rediz_test_config import REDIZ_TEST_CONFIG

EXACTABLE_FOX = REDIZ_TEST_CONFIG['EXACTABLE_FOX']


def test_emails():
    email = 'peter.cotton@microprediction.com'
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    write_key = EXACTABLE_FOX
    rdz.set_email(write_key=write_key, email=email)
    code = rdz.shash(write_key)
    email_back_1 = rdz._get_email(code)
    email_back_2 = rdz._get_email(write_key)
    assert email_back_1==email
    assert email_back_2==email
    rdz.delete_email(write_key=write_key)
    email_back_3 = rdz._get_email(rdz.shash(write_key))
    assert email_back_3 is None

