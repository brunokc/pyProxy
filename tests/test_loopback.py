import logging

import pytest

from pyproxy.httpserver import HttpServer

LOOPBACK = "127.0.0.1"
# These shouldn't matter we they won't be used
HTTP_SERVER_PORT = 0
PROXY_PORT = 0

_LOGGER = logging.getLogger(__name__)

class TestLoopbackDetection:
    def test_ip_in_127_0_0_0_network(self):
        server = HttpServer(LOOPBACK, PROXY_PORT)
        assert server.is_loopback("127.0.0.1")
        assert server.is_loopback("127.0.0.3")
        assert server.is_loopback("127.0.1.1")
        assert server.is_loopback("127.1.2.3")

    def test_localhost(self):
        server = HttpServer(LOOPBACK, PROXY_PORT)
        assert server.is_loopback("localhost")
        assert not server.is_loopback("loopback")

    def test_hostname(self):
        server = HttpServer(LOOPBACK, PROXY_PORT)
        assert not server.is_loopback("foo")
        assert not server.is_loopback("foo.com")
