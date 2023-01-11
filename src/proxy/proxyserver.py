import asyncio

from proxy.httpserver import HttpServer, ProxyMode
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
        self._proxy_mode = None

    def register_callback(self, callback: ProxyServerCallback, proxy_mode: ProxyMode):
        self._callback = callback
        self._proxy_mode = proxy_mode

    async def run(self):
        wsserver = WebSocketServer(WS_IP, WS_PORT)
        server = HttpServer(self._address, self._port, wsserver)
        server.register_callback(self._callback, self._proxy_mode)

        await asyncio.gather(server.run(), wsserver.run())
