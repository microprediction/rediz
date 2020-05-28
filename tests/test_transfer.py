from rediz.client import Rediz
from rediz.rediz_test_config import REDIZ_TEST_CONFIG


def test_transfers():
    do_test_transfer(source_balance=0.0,  recipient_balance=-100.0, amount=10.0, expected_given=10.0, expected_success=1)
    do_test_transfer(source_balance=50.0, recipient_balance=50.0,   amount=20.0, expected_given=0.0, expected_success=0)


def do_test_transfer(source_balance, recipient_balance,amount, expected_given, expected_success):
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    source       = '9e716ad7649a44a2bf1d522ffe7d86c2'
    recipient    = '5e4d88d46f54009ff2fdee07b62f6a75'
    rdz.client.hset(name=rdz._BALANCES, key=recipient, value=recipient_balance )
    rdz.client.hset(name=rdz._BALANCES, key=source,    value=source_balance )
    report = rdz.transfer(source_write_key=source, recipient_write_key=recipient,amount=amount, as_record=True )
    assert report['success']==expected_success
    if report['success']:
        assert report['given']==expected_given
        assert abs(report['received']-report['given']*rdz._DISCOUNT)<1e-6,'discount wrong'
        new_source_balance = rdz.get_balance(source)
        new_recipient_balance = rdz.get_balance(recipient)
        assert abs( new_source_balance- (source_balance-report['given']) )<1e-5
        assert abs( new_recipient_balance - (report['received'] + recipient_balance) ) < 1e-5
    rdz.client.hdel(rdz._BALANCES,source, recipient)
