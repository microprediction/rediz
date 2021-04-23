
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from pprint import pprint


SURE = True


if __name__ == '__main__':
    rdz     = Rediz(**REDIZ_COLLIDER_CONFIG)
    ownership = rdz.client.hgetall(rdz._OWNERSHIP)

    PLAYERS = {'Hikaru': 'hikaru_nakamura',
               'Firouzja2003': 'alireza_firouzja',
               'GMWSO': 'wesley_so',
               'LyonBeast': 'maxime_vachier_lagrave',
               'nihalsarin': 'nihal_sarin',
               'DanielNaroditsky': 'daniel_naroditsky',
               'PinIsMightier': 'halloween_gambit'}

    URL_TEMPLATE = 'https://api.chess.com/pub/player/HANDLE/stats'
    CATEGORIES = ['chess_blitz', 'chess_bullet']

    if __name__ == '__main__':
        # Chess.Com ratings
        names_to_delete = list()
        for category in CATEGORIES:
            for handle, player in PLAYERS.items():
                name = category + '_' + handle + '.json'
                print(name)
                names_to_delete.append(name)

    if SURE:
        for name in names_to_delete:
            resultz = rdz._delete_implementation(names=names_to_delete)

