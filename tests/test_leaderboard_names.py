from rediz.conventions import RedizConventions
import datetime

def test_custom_leaderboard_names():
    rc = RedizConventions()
    questions = [ {'name':'z1~cop.json','sponsor':'big bird'},
                  {'name': 'z1~cop.json', 'sponsor': 'big bird','dt':datetime.date(2019, 4, 13)},
                  {'sponsor': 'big bird'},
                  {'sponsor': 'big bird', 'dt': datetime.date(2019, 4, 13)}
                  ]
    answers   = [ rc.CUSTOM_LEADERBOARD + 'big_bird::zscores_univariate::all_time.json',
                  rc.CUSTOM_LEADERBOARD + 'big_bird::zscores_univariate::2019-04.json',
                  rc.CUSTOM_LEADERBOARD + 'big_bird::all_streams::all_time.json',
                  rc.CUSTOM_LEADERBOARD + 'big_bird::all_streams::2019-04.json',
                  ]

    for q,a in zip(questions,answers):
        a1 = rc.custom_leaderboard_name(**q)
        assert a1==a

