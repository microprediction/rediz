from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from flask import jsonify, Flask

app = Flask(__name__)

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    res1 = rdz.get_summary(name='die.json')
    red2 = rdz.get_summary(name='cop.json')
    with app.app_context():
        jsonify(res1)




