import asyncio

from .httpserver import HttpServer
from .callback import ProxyServerCallback

class ProxyServer:
    _callback: ProxyServerCallback

    def __init__(self, address: str, port: int):
        self._address = address
        self._port = port

    def register_callback(self, callback: ProxyServerCallback) -> None:
        self._callback = callback

    async def run(self) -> None:
        server = HttpServer(self._address, self._port)
        server.register_callback(self._callback)
        await server.run()
