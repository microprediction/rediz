
import time
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from rediz.client import Rediz
import asyncio
import aiohttp
import json
import datetime
import pprint

## TODO: Modify so this calls the Algorithmia API rather than Rediz directly
## TODO: Move it to algoz ?!

async def fetch(session, url):
    async with session.get(url) as response:
        if response.status != 200:
            response.raise_for_status()
        return await response.text()

async def fetch_all(session, urls):
    tasks = []
    for url in urls:
        task = asyncio.create_task(fetch(session, url))
        tasks.append(task)
    results = await asyncio.gather(*tasks)
    return results

async def fetch_prices(symbols):
    urls = [ REDIZ_COLLIDER_CONFIG["template_url"].replace("SYMBOL",symbol) for symbol in symbols ]
    async with aiohttp.ClientSession() as session:
        results = await fetch_all(session, urls)
    prices = [json.loads(r).get('Global Quote')['05. price'] for r in results]
    return prices

def collider_prices():
    symbols = REDIZ_COLLIDER_CONFIG["symbols"]
    try:
        prices =  asyncio.run( fetch_prices(symbols=symbols ) )
        return {"names":[ s+'.json' for s in symbols],"values":list(map(float,prices))}
    except:
        return None

def set_collider_values(rdz,change_data):
    if change_data:
        budgets = [ 100 for _ in change_data["values"]]
        write_keys = [ REDIZ_COLLIDER_CONFIG["write_key"] for _ in change_data["values"] ]
        change_data.update({"budgets":budgets,"write_keys":write_keys})
        res = rdz.mset(**change_data)
        print("Got data")
    else:
        print("Missing data")



def example_feed():
    rdz = Rediz(**REDIZ_COLLIDER_CONFIG)
    HOURS_TO_RUN = 10000000
    previous_data = None
    offset = time.time() % 60
    start_time = time.time()
    closed = False
    cold   = True
    while time.time() < start_time + HOURS_TO_RUN * 60 * 60:
        if abs(time.time() % 60 - offset) < 1:
            data = collider_prices() or collider_prices() or collider_prices()
            down = data is None
            if not down:
                print(data)
                if cold:
                    previous_data = data.copy()
                    time.sleep(15)
                num = len(data["values"])
                changes = [ 100.*(data["values"][k] - previous_data["values"][k]) for k in range(num)]
                changed = any( [abs(c)>1e-4 for c in changes ] )
                if not changed and not cold:
                    closed = True
                    print("Market is closed")
                if changed:
                    change_data = {"names": data["names"], "values": changes}
                    previous_data = data.copy()
                    set_before = time.time()
                    set_collider_values(rdz=rdz, change_data=change_data)
                    set_after = time.time()
                    print("Set() took " + str(set_after - set_before) + " seconds.")
                    pprint.pprint(change_data)
                    time.sleep(10)
                cold = False
            if closed:
                rdz.mtouch(names=data["names"], budgets=[1 for _ in data["names"]])
                print(datetime.datetime.now())
            time.sleep(10)
        else:
            time.sleep(0.5)

if __name__ == '__main__':
    example_feed()


