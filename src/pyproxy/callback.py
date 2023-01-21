from enum import IntEnum

class ProxyServerAction(IntEnum):
    Forward = 1
    Intercept = 2


class ProxyServerCallback:
    async def on_new_request_async(self, request) -> ProxyServerAction:
        print("ProxyServerCallback:on_new_request_async: returning ProxyServerAction.Forward")
        return ProxyServerAction.Forward

    async def on_new_response_async(self, response) -> ProxyServerAction:
        print("ProxyServerCallback:on_new_response_async: returning ProxyServerAction.Forward")
        return ProxyServerAction.Forward
