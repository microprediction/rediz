from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, FLASHY_COYOTE

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    rdz.cancel(name='mtum.json',delay=rdz.DELAYS[0],write_key=FLASHY_COYOTE)
