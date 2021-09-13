
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, CELLOSE_BOBCAT, OFFCAST_GOOSE, EMBLOSSOM_MOTH
from pprint import pprint, pformat
import datetime

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    sponsor = EMBLOSSOM_MOTH
    code = rdz.code_from_code_or_key(sponsor)
    lb = rdz._get_custom_leaderboard_implementation(sponsor_code=code, dt=datetime.datetime.now(), count=200,
                                                           with_repos=False, readable=False)
    pprint(lb)

    # Hardwired list of possible winners
    EMAILS = rdz._obscurity + "emails"
    rdz.client.hset(name=EMAILS,key="0d50ea91e7ce812189011782de0696fa",value='peter.cotton@microprediction.com')

    # Email the winner
    winner = next(iter(lb))
    winner_email = rdz.client.hget(name=EMAILS, key=winner)
    if winner_email is not None:
        tmp_key = rdz.create_key(difficulty=6)
        tmp_code = rdz.code_from_code_or_key(tmp_key)
        tmp_animal = rdz.animal_from_code(tmp_code)
        winner_message = {'prize':100,
               'issued':datetime.datetime.now().strftime('%Y/%m/%d'),
               'redeem key':tmp_key,
               'instructions':'Email payments@microprediction.com and copy this message'}
        payer_message = {'prize': 100,
                          'issued': datetime.datetime.now().strftime('%Y/%m/%d'),
                          'email': winner_email,
                          'redeem animal':tmp_animal,
                          'redeem verification url':'https://www.muid.org/validate/PUTKEYHERE',
                         'instructions': 'Check redeem animal. One prize per day only.',
                         }

        pprint(winner_message)
        pprint(payer_message)

        import requests
        import json
        winner_text = pformat(winner_message)
        payer_text = pformat(payer_message)
        res = requests.get(url="http://alerts.microprediction.org/awardemail?to="+winner_email+"&text="+winner_text+"&subject=This email contains a redemption key worth one hundred dollars")
        res = requests.get(url="http://alerts.microprediction.org/awardemail?to=payments@microprediction.com&text=" + payer_text + "&subject=prize "+payer_message['issued']+' '+tmp_animal+' '+winner_email)

        pprint(res)





