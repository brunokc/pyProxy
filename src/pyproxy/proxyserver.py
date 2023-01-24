import asyncio

from .httpserver import HttpServer
from .callback import ProxyServerCallback

class ProxyServer:
    def __init__(self, address, port):
        self._address = address
        self._port = port
        self._wsserver = None
        self._callback = None

    def register_callback(self, callback: ProxyServerCallback):
        self._callback = callback

    async def run(self):
        server = HttpServer(self._address, self._port)
        server.register_callback(self._callback)
        await server.run()
