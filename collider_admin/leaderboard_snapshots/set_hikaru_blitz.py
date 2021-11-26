
from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, DOOMSDAY_STOAT, BOOZE_LEECH, DATABLE_LLAMA,\
    DOODLE_MAMMAL, MESOLE_MAMMAL, SOSHED_BOA, SMEECH_CLAM, ODSO_EAGLE, FLASHY_COYOTE, TAMELESS_FLY, BELLEHOOD_FOX, HEALTHY_EEL, GLOTTAL_SLOTH
from pprint import pprint

if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    pprint(rdz.client.hgetall(rdz._EMAILS))
    name = "chess_blitz_change_Hikaru.json"
    res = rdz.set(name=name,value=-3,write_key=DOOMSDAY_STOAT, budget=0.01)
    #pprint(res)

    delay = 70

    lb = rdz.get_leaderboard(name=name, delay=delay, count=5, readable=False)
    pprint(lb)

    write_keys = [BOOZE_LEECH, TAMELESS_FLY, ODSO_EAGLE, SMEECH_CLAM, FLASHY_COYOTE, DATABLE_LLAMA, SMEECH_CLAM, ODSO_EAGLE, FLASHY_COYOTE, TAMELESS_FLY]
    status = [ (write_key, rdz.is_active(write_key=write_key, names=[name], delays=[rdz.DELAYS[0]] )) for write_key in write_keys ]
    pprint(status)

    delay = rdz.DELAYS[0]
    print(delay)
    son = rdz._sample_owners_name(name=name, delay=rdz.DELAYS[0])
    owners = rdz.client.smembers(son)
    pprint(son)
    print(owners)

    sn = rdz._samples_name(name=name, delay=rdz.DELAYS[0])
    smples = rdz.client.zrange(name=sn, start=0, end=-1)
    some= list(set([ spl[10:] for spl in smples ]))

    print('Who is in')
    pprint(some)




