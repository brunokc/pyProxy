import json
import logging
from aiohttp import web, WSMsgType
from enum import Enum

_LOGGER = logging.getLogger(__name__)

class StreamDirection(Enum):
    Outgoing = 1,
    Incoming = 2


class WebSocketStream:
    def __init__(self, ws, direction: StreamDirection):
        self.ws = ws
        self.direction = direction
        if direction == StreamDirection.Incoming:
            self.data = b"<\r\n"
        else:
            self.data = b">\r\n"

    def write(self, data: bytes):
        if not self.ws.closed:
            self.data += data

    def close(self):
        pass

    async def drain(self):
        if not self.ws.closed:
            await self.ws.send_bytes(self.data)
            self.data = b""


class WebSocketServer:
    def __init__(self, address, port):
        self._address = address
        self._port = port
        self._intercept_clients = {}

    def get_streams(self, host):
        streams = (None, None)
        if host in self._intercept_clients:
            ws = self._intercept_clients[host]
            if ws is not None:
                streams = (
                    WebSocketStream(ws, StreamDirection.Incoming),
                    WebSocketStream(ws, StreamDirection.Outgoing)
                    )

        return streams

    async def handle_command(self, data, ws, clientip, port):
        if data["command"].lower() == "listen":
            args = data["args"]
            host = args["host"]
            self._intercept_clients.update({ host: ws })
            _LOGGER.debug("registered LISTEN client for host %s (caller: %s:%d)",
                host, clientip, port)

    async def handle_binary(self, data):
        _LOGGER.debug("received binary payload")
        _LOGGER.debug(data)

    async def wshandler(self, request):
        peername = request.transport.get_extra_info("peername")
        if peername is not None:
            clientip, port = peername
        _LOGGER.debug(f"connection from %s:%d", clientip, port)

        ws = web.WebSocketResponse()
        await ws.prepare(request)

        async for msg in ws:
            _LOGGER.debug("new message %s", msg.__repr__())
            if msg.type == WSMsgType.TEXT:
                if msg.data == "close":
                    await ws.close()
                else:
                    await self.handle_command(json.loads(msg.data), ws, clientip, port)
            elif msg.type == WSMsgType.BINARY:
                await self.handle_binary(msg.data)
            elif msg.type == WSMsgType.ERROR:
                _LOGGER.debug("connection closed with exception %s", ws.exception())

        # if host in self._intercept_clients:
        #     del self._intercept_clients[host]

        _LOGGER.debug("connection closed")

    async def run(self):
        app = web.Application()
        app.add_routes([web.get("/ws", self.wshandler)])

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self._address, self._port)
        await site.start()
        _LOGGER.debug("serving on %s:%d", self._address, self._port)
