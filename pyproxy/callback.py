from abc import ABC, abstractmethod
from enum import IntEnum, auto

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

Note that there is no option to suppress a response to a client. Once a request
is made, even if suppressed on its way to the server, it must be responded back
to the client. If the request was suppressed on its way up, the handler becomes
responsible for generating a response.

"""

class ProxyServerAction(IntEnum):
    Forward = auto()
    Suppress = auto()


class ProxyServerCallback(ABC):
    @abstractmethod
    async def on_new_request_async(
        self,
        request: HttpRequest) -> ProxyServerAction:

        pass

    @abstractmethod
    async def on_new_response_async(
        self,
        action: ProxyServerAction,
        request: HttpRequest,
        response: HttpResponse) -> None:

        pass
