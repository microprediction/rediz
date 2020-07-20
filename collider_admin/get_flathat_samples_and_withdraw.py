from rediz.client import Rediz
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG, FLATHAT_STOAT
import pprint
import time

from rediz.collider_config_private import BOOZE_MAMMAL

def _entered():
    entered_in = list()
    for name in ['bart_delays.json', 'hospital_bike_activity']:
        for delay in rdz.DELAYS:
            owners = rdz._get_sample_owners(name=name, delay=delay)
            animals = [rdz.animal_from_key(key) for key in owners]
            if any('Flathat' in animal for animal in animals):
                entered_in.append((name, delay))
    return entered_in


if __name__ == '__main__':
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)

    pprint.pprint(_entered())

    delay = 310
    rdz._cancel_implementation(name='bart_delays.json', write_key=FLATHAT_STOAT, delay=delay )

    time.sleep(delay+5)
    pprint.pprint(_entered())

    if False:
        # if not working, trace into actual deletion ... but it looks like it is working.
        rdz._delete_scenarios_implementation(name='bart_delays.json', write_key=FlATHAT_STOAT, delay=delay)
        # It could be that the promise isn't/wasn't processed correctly, however, so _delete_scenarios never got called (though then there should be no cancellation confirm either)

    # Tentative conclusion: rdz._cancel_implementation  (which should probably be renamed withdraw) is working fine but maybe not called properly from flask
    # or from the microprediction client.


    pprint.pprint(_entered())



