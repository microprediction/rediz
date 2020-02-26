
import time
from rediz.collider_config_private import REDIZ_COLLIDER_CONFIG
from rediz.client import Rediz
import asyncio
import aiohttp
import json
import datetime
import pprint
import requests

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

def collider_prices(symbols):
    try:
        prices =  asyncio.run( fetch_prices(symbols=symbols ) )
        return {"names":[ s+'.json' for s in symbols],"values":list(map(float,prices))}
    except:
        return None

def set_collider_values_direct(rdz,change_data):
    if change_data:
        budgets = [ 100 for _ in change_data["values"]]
        write_keys = [ REDIZ_COLLIDER_CONFIG["write_key"] for _ in change_data["values"] ]
        change_data.update({"budgets":budgets,"write_keys":write_keys})
        res = rdz.mset(**change_data)
        print("Got data")
    else:
        print("Missing data")

def set_or_touch(names,write_keys,budgets, values=None, touch=True):
    """ Use web API to set or touch names """
    base_url = "microprediction.pythonanywhere.com/multi/"
    request_data = {"names": ",".join(names), "write_keys": ",".join(write_keys),
                    "budgets": ",".join([str(b) for b in budgets])}
    if touch:
        res = requests.put(base_url,data=request_data)
    else:
        if values:
            request_data.update( {"values":",".join( values)}  )
            res = requests.put(base_url, data=request_data)
        else:
            return None
    return res.status_code==200

def touch_collider_values(names, budgets, write_keys):
    base_url = "microprediction.pythonanywhere.com/multitouch/"
    cs_budgets = ",".join( budgets )
    cs_names   = ",".join( names )
    cs_write_keys = ",".join( write_keys )
    request_data = {"names":cs_names, "write_keys":cs_write_keys, "budgets":cs_budgets}
    res = requests.put(base_url, data=request_data)
    return res.status_code==200

def example_feed_config():
    rdz     = Rediz(**REDIZ_COLLIDER_CONFIG)
    symbols = REDIZ_COLLIDER_CONFIG["symbols"]
    names   = REDIZ_COLLIDER_CONFIG["names"]
    budgets = [ 200 for _ in names ]
    write_keys = [ REDIZ_COLLIDER_CONFIG["write_key"] for _ in names ]
    return names, symbols, write_keys, budgets



def example_feed():
    names, symbols, write_keys, budgets = example_feed_config()
    HOURS_TO_RUN = 10000000
    previous_data = None
    offset = time.time() % 60
    start_time = time.time()
    closed = False
    cold   = True
    the_names = None
    while time.time() < start_time + HOURS_TO_RUN * 60 * 60:
        if abs(time.time() % 60 - offset) < 1:
            data = collider_prices(symbols=symbols) or collider_prices(symbols=symbols) or collider_prices(symbols=symbols)
            down = data is None
            if not down:
                the_names = data["names"]
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
                    set_or_touch( touch=False, names=names, write_keys=write_keys, values=changes, budgets=budgets )
                    set_after = time.time()
                    print("Set() took " + str(set_after - set_before) + " seconds.")
                    pprint.pprint(change_data)
                    time.sleep(10)
                cold = False
            if closed:
                rdz.mtouch(names=the_names, budgets=[1 for _ in the_names])
                print(datetime.datetime.now())
            time.sleep(10)
        else:
            time.sleep(0.5)

if __name__ == '__main__':
    example_feed()


