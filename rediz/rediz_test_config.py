try:
    from rediz.rediz_test_config_private import REDIZ_TEST_CONFIG
    REDIZ_TEST_CONFIG.update({"decode_responses":True})
except:
    REDIZ_TEST_CONFIG = {"decode_responses":True}  # Could supply a redis instance config here
