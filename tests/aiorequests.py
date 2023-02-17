import aiohttp


async def get(url, *args, **kargs):
    async with aiohttp.ClientSession() as session:
        print("client session created")
        async with session.get(url, *args, **kargs) as response:
            print("get request issued")
            return response.status, await response.json()
