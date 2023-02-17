from typing import Union

from .callback import ProxyServerCallback
from .httprequest import HttpRequest, HttpResponse
from .httpserver import HttpServer, ProxyServerAction
from .stream import StreamReader


class AlwaysForwardProxyServerCallback(ProxyServerCallback):
    async def on_new_request_async(
        self, request: HttpRequest) -> Union[ProxyServerAction, StreamReader]:

        return ProxyServerAction.Forward

    async def on_new_response_async(
        self, request: HttpRequest, response: HttpResponse) -> Union[
            ProxyServerAction, StreamReader]:

        return ProxyServerAction.Forward


class ProxyServer:
    def __init__(self, address: str, port: int):
        self._server = HttpServer(address, port)

        # Default callback that just forwards requests over to the destination
        self._server.register_callback(AlwaysForwardProxyServerCallback())

    def register_callback(self, callback: ProxyServerCallback) -> None:
        self._server.register_callback(callback)

    async def close(self):
        if self._server:
            await self._server.close()

    async def run(self) -> None:
        await self._server.run()
