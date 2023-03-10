import asyncio
from datetime import datetime
import json
import logging
from time import mktime
from wsgiref.handlers import format_date_time

import pytest
from pytest_httpserver import HTTPServer

import aiorequests
from pyproxy import (
    HttpRequest, HttpResponse, ProxyServer, ProxyServerAction, ProxyServerCallback
)

LOOPBACK = "127.0.0.1"
HTTP_SERVER_PORT = 9998
PROXY_PORT = 9999

_LOGGER = logging.getLogger(__name__)

logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")

@pytest.fixture(scope="session")
def httpserver_listen_address():
    return (LOOPBACK, HTTP_SERVER_PORT)

@pytest.fixture
def aiorequest():
    return aiorequests.Requests(LOOPBACK, PROXY_PORT)

@pytest.fixture
async def proxy_server():
    server = ProxyServer(LOOPBACK, PROXY_PORT)
    server.set_options(allow_loopback_target=True)
    server_task = asyncio.create_task(server.run(), name="server")
    yield server
    await server.close()
    await asyncio.sleep(0.25)
    server_task.cancel()


class Callback(ProxyServerCallback):
    def __init__(self):
        self.requests = 0
        self.responses = 0
        self.action = ProxyServerAction.Forward

    def forward(self):
        self.action = ProxyServerAction.Forward

    def suppress(self):
        self.action = ProxyServerAction.Suppress

    async def on_new_request_async(
        self, request: HttpRequest) -> ProxyServerAction:
        self.requests += 1
        return self.action

    async def on_new_response_async(
        self,
        action: ProxyServerAction,
        request: HttpRequest,
        response: HttpResponse) -> None:

        callback_payload = json.dumps({ "message": "hello from callback" })

        now = datetime.now()
        stamp = mktime(now.timetuple())
        httpdate = format_date_time(stamp)

        response.http_version = request.version
        response.response_code = 200
        response.response_text = "OK"
        response.headers.clear()
        response.headers.update({
            "Content-Type": "application/json",
            "Date": httpdate
        })
        response.set_body(callback_payload.encode())


class TestRequestSuppression:
    async def test_request_suppressed(
        self, httpserver: HTTPServer, proxy_server, aiorequest):

        callback = Callback()
        callback.suppress()
        proxy_server.register_callback(callback)

        server_payload = { "message": "hello from server" }
        callback_payload = { "message": "hello from callback" }
        httpserver.expect_request("/hello").respond_with_json(server_payload)

        response = await aiorequest.get(httpserver.url_for("/hello"))
        assert response.status == 200
        responsejson = await response.json()
        assert responsejson != server_payload
        assert responsejson == callback_payload
