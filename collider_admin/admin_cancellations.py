from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    report = rdz.admin_cancellations( with_report=True )
