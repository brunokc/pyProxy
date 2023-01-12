import asyncio

from proxy.httpserver import HttpServer
from proxy.callback import ProxyServerCallback
from proxy.websocket import WebSocketServer

WS_IP = ""
WS_PORT = 8787

class ProxyServer:
    def __init__(self, address, port):
        self._address = address
        self._port = port
        self._wsserver = None
        self._callback = None

    def register_callback(self, callback: ProxyServerCallback):
        self._callback = callback

    async def run(self):
        wsserver = WebSocketServer(WS_IP, WS_PORT)
        server = HttpServer(self._address, self._port, wsserver)
        server.register_callback(self._callback)

        await asyncio.gather(server.run(), wsserver.run())
