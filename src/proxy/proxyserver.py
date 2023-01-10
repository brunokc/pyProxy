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
        # self._forward_to_host = None
        # self._forward_to_port = 80

    # def forward_to(self, host, port=80):
    #     self._forward_to_host = host
    #     self._forward_to_port = port

    def register_callback(self, callback: ProxyServerCallback, proxy_mode: ProxyMode):
        self._callback = callback
        self._proxy_mode = proxy_mode

    async def run(self):
        wsserver = WebSocketServer(WS_IP, WS_PORT)
        server = HttpServer(self._address, self._port, wsserver)
        # server.forward_to(self._forward_to_host, self._forward_to_port)
        server.register_callback(self._callback, self._proxy_mode)

        await asyncio.gather(server.run(), wsserver.run())
