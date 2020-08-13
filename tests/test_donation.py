import requests
from rediz.client import Rediz
from rediz.rediz_test_config import REDIZ_TEST_CONFIG


def test_donate():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    DONATION_PASSWORD = rdz.get_donation_password()
    ob = rdz._obscurity
    write_key_1 = '861f9f15d9d151b9f9e139532c9dca9d'
    write_key_2 = '3ea3788a1ef07a257b8608c7087287f0'

    res1 = rdz.donate(write_key=write_key_1,password=DONATION_PASSWORD, donor='me')
    rdz.donate(write_key=write_key_2,password=DONATION_PASSWORD, donor='you')

    donors = rdz.get_donors()
    assert len(list(donors.keys()))>1

def dont_test_donate_remote():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    DONATION_PASSWORD = rdz.get_donation_password()
    ob = rdz._obscurity
    write_key_1 = '861f9f15d9d151b9f9e139532c9dca9d'
    write_key_2 = '3ea3788a1ef07a257b8608c7087287f0'

    res1 = requests.post('https://api.microprediction.org/donations/' + write_key_1, data={'password': DONATION_PASSWORD,'donor':'Test'})
    res2 = requests.post('https://api.microprediction.org/donations/' + write_key_2, data={'password': DONATION_PASSWORD,'donor':'Test'})

    assert res1.json()['success']
