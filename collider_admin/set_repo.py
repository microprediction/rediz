
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, EXACTABLE_FOX, DOODLE_MAMMAL

URLS = {EXACTABLE_FOX:'https://github.com/microprediction/echochamber',
        DOODLE_MAMMAL:'https://gist.github.com/microprediction/7b1bcaae0eb012c5a51f0c2ce9c81246'}

if __name__=="__main__":
    for write_key, url in URLS.items():
        rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
        rdz.set_repository(write_key=write_key, url=url)
        url_back_1 = rdz.get_repository(rdz.shash(write_key))
        url_back_2 = rdz.get_repository(write_key)
        assert url_back_1==url
        assert url_back_2==url
        print(url_back_2)

