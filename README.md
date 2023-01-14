# pyProxy

A simple, programmatic HTTP proxy written in Python.

pyProxy was created to facilitate scenarios where one might need to intercept
HTTP traffic. It allows for programmatic control of HTTP traffic, allowing for
the supression, modification or forwarding of HTTP requests and responses as
they transit through pyProxy.

## Example

The canonical example just creates a proxy server on a particular IP address and
port and just forwards requests and responses as they arrive.

```python
from proxy.callback import ProxyServerCallback, ProxyServerAction
from proxy.proxyserver import ProxyServer

PROXY_IP = "127.0.0.1"
PROXY_PORT = 8080

server = ProxyServer(PROXY_IP, PROXY_PORT)
await server.run()
````

In a more useful example, users can register a callback that will be given the
opportunity to decide what to do with each request and response that goes through
the proxy.

```python
import asyncio

from proxy.callback import ProxyServerCallback, ProxyServerAction
from proxy.proxyserver import ProxyServer

PROXY_IP = "127.0.0.1"
PROXY_PORT = 8080

class RequestHandler(ProxyServerCallback):
    def __init__(self, proxy_ip: str, proxy_port: int):
        self.proxy_ip = proxy_ip
        self.proxy_port = proxy_port

    async def on_new_request(self, request):
        """Do something with the request here"""
        return ProxyServerAction.Forward

    async def on_new_response(self, response):
        """Do something with the response here"""
        return ProxyServerAction.Forward

    async def run(self):
        server = ProxyServer(PROXY_IP, PROXY_PORT)
        server.register_callback(self)
        await server.run()

if __name__ == "__main__":
    handler = RequestHandler(PROXY_IP, PROXY_PORT)
    try:
        asyncio.run(handler.run())
    except KeyboardInterrupt:
        print("Exiting.")
```
