import aiohttp


async def get(url, *args, **kargs):
    async with aiohttp.ClientSession() as session:
        async with session.get(url, *args, **kargs) as response:
            # Ensure response is read before the connection is closed
            await response.read()
            return response
