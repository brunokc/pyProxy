import aiohttp


class Requests:
    def __init__(self, proxy_ip: str, proxy_port: int):
        self._proxy_entry = { "proxy": f"http://{proxy_ip}:{proxy_port}" }

    async def get(self, url, *args, **kargs):
        async with aiohttp.ClientSession() as session:
            kargs.update(self._proxy_entry)
            async with session.get(url, *args, **kargs) as response:
                # Ensure response is read before the connection is closed
                await response.read()
                return response
