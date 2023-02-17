import asyncio
import logging

import aiorequests
import pytest
from pytest_httpserver import HTTPServer

from pyproxy.proxyserver import ProxyServer

OWN_IP = "192.168.1.182"
PROXY_IP = ""
PROXY_PORT = 8888

_LOGGER = logging.getLogger(__name__)

def setup_logging() -> None:
    logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")

@pytest.fixture(scope="session")
def httpserver_listen_address():
    return (OWN_IP, 8889)

class TestSimpleRequests:
    async def get(self, *args, **kargs):
        kargs.update({ "proxy": f"http://{OWN_IP}:{PROXY_PORT}" })
        _LOGGER.debug(f"kargs = {kargs}")
        return await aiorequests.get(*args, **kargs)

    @pytest.mark.asyncio
    async def test_simple_request(self, httpserver: HTTPServer, event_loop):
        setup_logging()
        server = ProxyServer(OWN_IP, PROXY_PORT)
        server_task = asyncio.create_task(server.run(), name="server")

        payload = { "message": "hello" }
        httpserver.expect_request("/hello").respond_with_json(payload)

        # client_task = asyncio.create_task(self.get(httpserver.url_for("/hello")))
        status, response = await self.get(httpserver.url_for("/hello"))
        # await asyncio.wait([server_task, client_task], return_when=asyncio.FIRST_COMPLETED)
        # await client_task
        # status, response = await asyncio.wait([client_task])

        # status, response = client_task.result()
        assert status == 200
        assert response == payload

        # Close server and allow it to exit
        await server.close()
        await asyncio.sleep(0.25)
