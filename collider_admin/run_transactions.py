from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
import pprint

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    transactions = rdz.get_transactions(write_key="collider-write-key-2e07a2a0-667b-4d38-a485-1be11bdef047")
    pprint.pprint(transactions)
    transactions = rdz.get(name="transactions::sq.json")
    pprint.pprint(transactions)
