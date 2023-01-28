import asyncio
import logging
from urllib.parse import urlparse, unquote, ParseResult
from asyncio.streams import StreamReader
from typing import Dict

from .stream import MemoryStreamReader

_LOGGER = logging.getLogger(__name__)


def parse_form_data(form_data):
    """Convert URL encoded HTML form data into a dictionary"""
    values = { k:unquote(v) for (k,v) in
        [entry.split(b"=") for entry in form_data.split(b"&")]
    }
    return values


class HttpRequestResponseBase:
    def __init__(self, reader: StreamReader):
        self._reader = reader
        self.headers: Dict[str, str] = { }
        self.body = b""

    async def _read_headers(self):
        try:
            # Read the request line and all the request headers
            return await self._reader.readuntil(b"\r\n\r\n")
        except asyncio.IncompleteReadError as e:
            return e.partial

    def _parse_headers(self, lines):
        self.headers.clear()
        for line in lines:
            if not line:
                break
            name, value = line.decode().split(": ")
            self.headers[name] = value

    def get_streamreader(self):
        if self.body:
            return MemoryStreamReader(self.body)
        else:
            return self._reader

    def get_content_length(self):
        return int(self.headers["Content-Length"]
            if "Content-Length" in self.headers else -1)

    async def read_body(self):
        if not self.body:
            self.body = await self._reader.readexactly(self.get_content_length())
        return self.body


class HttpRequest(HttpRequestResponseBase):
    raw_request: bytes
    method: str
    raw_url: str
    version: str
    url: ParseResult

    def __init__(self, addr, reader: StreamReader):
        super().__init__(reader)
        self.clientip, self.clientport = addr
        _LOGGER.debug("HttpRequest: clientip=%s, clientport=%d", self.clientip,
            self.clientport)

    async def read_headers(self):
        data = await self._read_headers()
        _LOGGER.debug(f"HttpRequest: received %s", data)
        if len(data) == 0:
            return 0

        self.raw_request = data
        http_request_lines = data.split(b"\r\n")

        # Split the request (first) line
        request_line = http_request_lines[0].decode()
        self.method, self.raw_url, self.version = request_line.split(" ")
        self.url = urlparse(self.raw_url)

        self._parse_headers(http_request_lines[1:])

        _LOGGER.debug("HttpRequest: %s", self)
        return len(data)

    def __str__(self):
        return str(dict(url=self.url, hostname=self.url.hostname, port=self.url.port,
            method=self.method))


class HttpResponse(HttpRequestResponseBase):
    raw_response: bytes
    http_version: str
    response_code: str
    response_text: str

    def __init__(self, reader: StreamReader):
        super().__init__(reader)

    async def read(self):
        data = await self._read_headers()
        _LOGGER.debug("HttpResponse: received %s", data)
        if len(data) == 0:
            return 0

        self.raw_response = data
        http_response_lines = data.split(b"\r\n")

        # Split the response (first) line
        response_line = http_response_lines[0].decode()
        self.http_version, self.response_code, self.response_text = response_line.split(" ")

        self._parse_headers(http_response_lines[1:])

    def __str__(self):
        return str(dict(http_version=self.http_version,
            response_code=self.response_code, response_text=self.response_text))
