import asyncio
import logging

import pytest
from pytest_httpserver import HTTPServer

import aiorequests
from pyproxy.proxyserver import ProxyServer

LOOPBACK = "127.0.0.1"
HTTP_SERVER_PORT = 9998
PROXY_PORT = 9999

_LOGGER = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")

@pytest.fixture(scope="session")
def httpserver_listen_address():
    _LOGGER.debug(">>> httpserver_listen_address")
    return (LOOPBACK, HTTP_SERVER_PORT)

@pytest.fixture
def aiorequest():
    _LOGGER.debug(">>> aiorequest")
    return aiorequests.Requests(LOOPBACK, PROXY_PORT)

@pytest.fixture
async def proxy_server():
    _LOGGER.debug(">>> proxy_server")
    server = ProxyServer(LOOPBACK, PROXY_PORT)
    server_task = asyncio.create_task(server.run(), name="server")
    yield server
    await server.close()
    await asyncio.sleep(0.25)
    server_task.cancel()


class TestSimpleRequests:
    async def test_simple_request(self, httpserver: HTTPServer, proxy_server, aiorequest):
        payload = { "message": "hello" }
        httpserver.expect_request("/hello").respond_with_json(payload)

        response = await aiorequest.get(httpserver.url_for("/hello"))
        assert response.status == 200
        assert await response.json() == payload
