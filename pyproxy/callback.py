from asyncio.streams import StreamReader
from enum import IntEnum
from typing import Union

from .httprequest import HttpRequest, HttpResponse

"""

----------
| Server |
----------
    ^  |
    |  |     -----------------
    |  +---> |               |
    +------- |               |
             | Proxy Handler |
    +------> |               |
    |  +---- |               |
    |  |     -----------------
    |  v
----------
| Client |
----------

For new requests, the proxy handler options are:

- Handler forwards request to server as-is (default) and awaits response
- Handler intercepts request, modifies or replaces it and forwards to server
- Handler suppresses request to server and returns response to client by itself

For server response, the handler options are:

- Handler forwards response to client as-is (default)
- Handler intercepts response, modifies or replaces it and has it forwarded to client

"""

class ProxyServerAction(IntEnum):
    Forward = 1


class ProxyServerCallback:
    async def on_new_request_async(
        self, request: HttpRequest) -> Union[ProxyServerAction, StreamReader]:

        print("ProxyServerCallback:on_new_request_async: returning ProxyServerAction.Forward")
        return ProxyServerAction.Forward

    async def on_new_response_async(
        self, request: HttpRequest, response: HttpResponse) -> Union[
            ProxyServerAction, StreamReader]:

        print("ProxyServerCallback:on_new_response_async: returning ProxyServerAction.Forward")
        return ProxyServerAction.Forward
