from enum import IntEnum

class ProxyServerAction(IntEnum):
    Forward = 1
    Intercept = 2


class ProxyServerCallback:
    async def on_new_request(self, request) -> ProxyServerAction:
        print("ProxyServerCallback:on_new_request: returning ProxyServerAction.Forward")
        return ProxyServerAction.Forward

    async def on_new_response(self, response) -> ProxyServerAction:
        print("ProxyServerCallback:on_new_response: returning ProxyServerAction.Forward")
        return ProxyServerAction.Forward
