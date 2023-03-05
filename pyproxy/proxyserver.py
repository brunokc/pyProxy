from typing import Union

from .callback import ProxyServerCallback
from .httpserver import HttpServer


class ProxyServer:
    def __init__(self, address: str, port: int):
        self._server = HttpServer(address, port)

    def register_callback(self, callback: ProxyServerCallback) -> None:
        self._server.register_callback(callback)

    def set_options(self, **kwargs):
        self._server.set_options(**kwargs)

    async def close(self) -> None:
        if self._server:
            await self._server.close()

    async def run(self) -> None:
        await self._server.run()
