from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG

example_name = 'electricity-fueltype-nyiso-wind.json'


if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    owner = rdz._authority(name=example_name)
    assert rdz.animal_from_key(owner)=='Offcast Goose'

    names = [n for n,_ in rdz.get_budgets().items() if 'electricity' in n]

    print(names)

    pipe = rdz.client.pipeline()
    for name in names:
        pipe.hset(name=rdz._ownership_name(), key=name, value=owner)
    res = pipe.execute()
    print(res)

    # Check
    for name in names:
        print(rdz.animal_from_key(rdz._authority(name)))




