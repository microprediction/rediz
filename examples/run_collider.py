
import requests, time
from rediz.collider_config_private import COLLIDER_CONFIG
from rediz.redis_config import REDIZ_CONFIG
from rediz.client import Rediz
import asyncio
import aiohttp
import json
import numpy as np

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
    urls = [ COLLIDER_CONFIG["template_url"].replace("SYMBOL",symbol) for symbol in symbols ]
    async with aiohttp.ClientSession() as session:
        results = await fetch_all(session, urls)
    prices = [json.loads(r).get('Global Quote')['05. price'] for r in results]
    return prices

def collider_prices():
    symbols = COLLIDER_CONFIG["symbols"]
    try:
        prices =  asyncio.run( fetch_prices(symbols=symbols ) )
        return {"names":[ s+'.json' for s in symbols],"values":list(map(float,prices))}
    except:
        return None

def set_collider_prices(rdz):
    data = collider_prices()
    if data:
        budgets = [ 100 for _ in data["values"]]
        write_keys = [ COLLIDER_CONFIG["write_key"] for _ in data["values"] ]
        data.update({"budgets":budgets,"write_keys":write_keys})
        res = rdz.mset(**data)
        print("Got data")
    else:
        print("Missing data")


def model(rdz):
    data  = collider_prices()
    if data:
        delay     = rdz.DELAYS[0]
        scenarios = list(np.random.randn(rdz.NUM_PREDICTIONS))
        MODEL_write_key = "3fa97bd9-8624-46da-99c8-0314af150298"
        for name in data["names"]:
            rdz.predict(name=name,values=scenarios,write_key=MODEL_write_key,delay=delay)
        print("Made predictions")


if __name__ == '__main__':
    rdz = Rediz(**REDIZ_CONFIG)
    set_collider_prices(rdz)
    time.sleep(1)
    set_collider_prices(rdz)
    for k in range(500):
        if k % 10 ==0:
            set_before = time.time()
            set_collider_prices(rdz)
            set_after = time.time()
            print("Set() took "+ str(set_after-set_before)+ " seconds.")
        time.sleep(0.1)
        model(rdz)
        rdz.admin_promises()
        time.sleep(1)




