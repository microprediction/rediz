
import time
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from rediz.client import Rediz
import asyncio
import aiohttp
import json
import datetime

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
    last_time = start_time
    while time.time() < start_time + HOURS_TO_RUN * 60 * 60:
        if abs(time.time() % 60 - offset) < 5:
            data = collider_prices() or collider_prices()
            if data:
                num = len(data["names"])
                if previous_data is not None:
                    changes = [data["values"][k] - previous_data["values"][k] for k in range(num)]
                else:
                    changes = [0 for k in range(num)]
                changes = [1000. * c for c in changes]
                change_data = {"names": data["names"], "values": changes}
                if any( [abs(c)>1e-4 for c in changes ] ):
                    print(data)
                    print(changes)
                    print(datetime.datetime.now())
                    set_before = time.time()
                    # Rescale
                    set_collider_values(rdz=rdz, change_data=change_data)
                    set_after = time.time()
                    print("Set() took " + str(set_after - set_before) + " seconds.")
                    previous_data = data.copy()
                    last_time = time.time()
                    time.sleep(10)
                else:
                    rdz.mtouch(names=data["names"], budgets=[1 for _ in data["names"]])
                    time.sleep(5)
                if (time.time()-last_time>15*60):
                    # Heartbeat
                    print(datetime.datetime.now())
                    last_time = time.time()
        else:
            time.sleep(1)

if __name__ == '__main__':
    example_feed()


