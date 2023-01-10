import json
from aiohttp import web, WSMsgType
from enum import Enum

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
            print(f"WebSocket: registered LISTEN client for host {host} (caller: {clientip}:{port})")

    async def handle_binary(self, data):
        print("WebSocket: received binary payload")
        print(data)

    async def wshandler(self, request):
        peername = request.transport.get_extra_info("peername")
        if peername is not None:
            clientip, port = peername
        print(f"WebSocket: connection from {clientip}:{port}")

        ws = web.WebSocketResponse()
        await ws.prepare(request)

        async for msg in ws:
            print(f"WebSocket: new message {msg!r}")
            if msg.type == WSMsgType.TEXT:
                if msg.data == "close":
                    await ws.close()
                else:
                    await self.handle_command(json.loads(msg.data), ws, clientip, port)
            elif msg.type == WSMsgType.BINARY:
                await self.handle_binary(msg.data)
            elif msg.type == WSMsgType.ERROR:
                print(f"WebSocket: connection closed with exception {ws.exception()}")

        # if host in self._intercept_clients:
        #     del self._intercept_clients[host]

        print("WebSocket: connection closed")

    async def run(self):
        app = web.Application()
        app.add_routes([web.get("/ws", self.wshandler)])

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, self._address, self._port)
        await site.start()
        print(f"WebSocket: serving on {self._address}:{self._port}")
