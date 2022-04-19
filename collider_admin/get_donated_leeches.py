from rediz.client import Rediz
import pprint
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG



if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    print('12:')
    pprint.pprint([ pair for pair in rdz.get_donations(with_key=True,len=12) if 'Leech' in pair[1]])
    print('13:')
    pprint.pprint([pair for pair in rdz.get_donations(with_key=True, len=13) if 'Leech' in pair[1]])