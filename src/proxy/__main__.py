import asyncio

from proxy.proxyserver import ProxyServer, ProxyMode
from proxy.callback import ProxyServerCallback, ProxyServerAction

PROXY_IP = ""
PROXY_PORT = 8080

class ProxyCallback(ProxyServerCallback):
    async def on_new_request(self, request) -> ProxyServerAction:
        print("ProxyCallback:on_new_request: returning ProxyServerAction.Forward")
        return ProxyServerAction.Forward

    async def on_new_response(self, response) -> ProxyServerAction:
        print("ProxyCallback:on_new_response: returning ProxyServerAction.Forward")
        return ProxyServerAction.Forward


if __name__ == "__main__":
    import sys

    server = ProxyServer(PROXY_IP, PROXY_PORT)
    callback = ProxyCallback()
    server.register_callback(callback, ProxyMode.Intercept)
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("Exiting.")
