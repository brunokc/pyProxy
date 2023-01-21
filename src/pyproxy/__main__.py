import asyncio
import logging

from .proxyserver import ProxyServer
from .callback import ProxyServerCallback, ProxyServerAction

PROXY_IP = ""
PROXY_PORT = 8080

_LOGGER = logging.getLogger(__name__)
print("name: ", __name__)

def setup_logging():
    _LOGGER.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)
    _LOGGER.addHandler(ch)

class ProxyCallback(ProxyServerCallback):
    async def on_new_request(self, request) -> ProxyServerAction:
        print("ProxyCallback:on_new_request: returning ProxyServerAction.Forward")
        return ProxyServerAction.Forward

    async def on_new_response(self, response) -> ProxyServerAction:
        print("ProxyCallback:on_new_response: returning ProxyServerAction.Forward")
        return ProxyServerAction.Forward


if __name__ == "__main__":
    setup_logging()
    server = ProxyServer(PROXY_IP, PROXY_PORT)
    callback = ProxyCallback()
    server.register_callback(callback)
    try:
        asyncio.run(server.run())
    except KeyboardInterrupt:
        print("Exiting.")
