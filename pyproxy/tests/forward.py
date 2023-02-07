import asyncio

from pyproxy.proxyserver import ProxyServer

PROXY_IP = ""
PROXY_PORT = 8080

if __name__ == "__main__":
    import sys

    server = ProxyServer(PROXY_IP, PROXY_PORT)

    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("Exiting.")
