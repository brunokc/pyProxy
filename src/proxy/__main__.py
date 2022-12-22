import asyncio

from proxy.proxy import RequestHandler
from proxy.websocket import WebSocketServer

PROXY_IP = ""
PROXY_PORT = 8080
WS_IP = "192.168.1.182"
WS_PORT = 8787

async def main(args):
    wsserver = WebSocketServer(WS_IP, WS_PORT)

    server = RequestHandler(PROXY_IP, PROXY_PORT, wsserver)
    server.forward_to(args[1], args[2])

    await asyncio.gather(server.run(), wsserver.run())

if __name__ == "__main__":
    import sys

    try:
        asyncio.run(main(sys.argv))
    except KeyboardInterrupt:
        print("Exiting.")
