from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, HEBDOMAD_LEECH


if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    for i in range(1000):
        rdz.touch(name='r_'+str(i)+'.json', budget=10.0, write_key=HEBDOMAD_LEECH)
        rdz.touch(name='xray_' + str(i) + '.json', budget=10.0, write_key=HEBDOMAD_LEECH)
    print(HEBDOMAD_LEECH)



