import asyncio
from enum import IntEnum

from proxy.httpserver import HttpServer
from proxy.websocket import WebSocketServer

PROXY_IP = ""
PROXY_PORT = 8080
WS_IP = "192.168.1.182"
WS_PORT = 8787

class ProxyMode(IntEnum):
    ListenIn = 1
    Intercept = 2

class ProxyServer:
    def __init__(self, address, port):
        self._address = address
        self._port = port

    async def run(self):
        wsserver = WebSocketServer(WS_IP, WS_PORT)
        server = HttpServer(self._address, self._port, wsserver)
        # server.forward_to(args[1], args[2])

        await asyncio.gather(server.run(), wsserver.run())
