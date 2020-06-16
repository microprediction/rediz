from rediz import Rediz
from rediz.rediz_test_config import REDIZ_TEST_CONFIG

def test_i_am_writing_tests_while_watching_ozark():
    conv = Rediz(**REDIZ_TEST_CONFIG)
    assert Rediz.sep() == '::'
    assert conv.SEP == '::'
    assert Rediz.tilde() == '~'
    assert conv.TILDE== '~'


