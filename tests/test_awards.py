from rediz.admin_client import AdminRediz
from rediz.client import Rediz
from rediz.rediz_test_config import REDIZ_TEST_CONFIG
from microconventions import MicroConventions

EXACTABLE_FOX = REDIZ_TEST_CONFIG['EXACTABLE_FOX']

def test_awards():
    rdz = Rediz(**REDIZ_TEST_CONFIG)
    admin_rdz = AdminRediz(**REDIZ_TEST_CONFIG)

    write_key = EXACTABLE_FOX
    public_write_key = MicroConventions.shash(write_key)

    # Add initial awards
    award_dict = {
        "bivariate": 500,
        "trivariate": 1000,
    }
    admin_rdz.add_award(write_key=public_write_key, award_dict=award_dict)
    assert rdz.get_awards(write_key) == award_dict

    # Add another award
    award_dict_2 = {
        "regular": 250,
    }
    admin_rdz.add_award(write_key=public_write_key, award_dict=award_dict_2)
    award_dict.update(award_dict_2)
    assert rdz.get_awards(write_key) == award_dict

    # Test deletion
    admin_rdz.remove_award(write_key=public_write_key, award_name="bivariate")
    admin_rdz.remove_award(write_key=public_write_key, award_name="trivariate")
    admin_rdz.remove_award(write_key=public_write_key, award_name="regular")
    assert rdz.get_awards(write_key) == {}

    print("All passed.")

if __name__ == '__main__':
    test_awards()