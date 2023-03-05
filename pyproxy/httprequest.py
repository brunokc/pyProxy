import asyncio
from asyncio.streams import StreamReader
import logging
from typing import Dict, List, Tuple
from urllib.parse import ParseResult, unquote, urlparse

from .const import *
from .stream import MemoryStreamReader

_LOGGER = logging.getLogger(__name__)


def parse_form_data(form_data: bytes) -> Dict[bytes, str]:
    """Convert URL encoded HTML form data into a dictionary"""
    values = { k:unquote(v) for (k,v) in
        [entry.split(b"=") for entry in form_data.split(b"&")]
    }
    return values


class HttpMessageBase:
    def __init__(self, reader: StreamReader):
        self._reader = reader
        self._start_line: str
        self._headers: Dict[str, str] = { }
        self._body = b""
        self._dirty = False

    async def _read_headers(self) -> bytes:
        try:
            # Read the request line and all the request headers
            return await self._reader.readuntil(CRLF + CRLF)
        except asyncio.IncompleteReadError as e:
            return e.partial

    def _parse_headers(self, lines: List[bytes]) -> None:
        self._headers.clear()
        for line in lines:
            if not line:
                break
            name, value = line.decode().split(": ")
            self._headers[name] = value

    @property
    def headers(self):
        return self._headers

    def get_streamreader(self) -> StreamReader:
        if self._body:
            return MemoryStreamReader(self._body)
        else:
            return self._reader

    def get_content_length(self) -> int:
        return int(self._headers[CONTENT_LENGTH]
            if CONTENT_LENGTH in self._headers else -1)

    async def read_body(self) -> bytes:
        if not self._body:
            self._body = await self._reader.readexactly(self.get_content_length())
        return self._body

    def set_body(self, body: bytes) -> None:
        self._body = body
        if CONTENT_LENGTH in self._headers:
            self._headers[CONTENT_LENGTH] = len(body)
        self._dirty = True


class HttpRequest(HttpMessageBase):
    raw_request: bytes
    method: str
    raw_url: str
    version: str
    url: ParseResult

    def __init__(self, addr: Tuple[str, int], reader: StreamReader):
        super().__init__(reader)
        self.clientip, self.clientport = addr
        _LOGGER.debug("HttpRequest: clientip=%s, clientport=%d", self.clientip,
            self.clientport)

    async def read_headers(self) -> int:
        data = await self._read_headers()
        _LOGGER.debug(f"HttpRequest: received %s", data)
        if len(data) == 0:
            return 0

        self.raw_request = data
        http_request_lines = data.split(CRLF)

        # Split the request (first) line
        self._start_line = http_request_lines[0].decode()
        self.method, self.raw_url, self.version = self._start_line.split(" ")
        self.url = urlparse(self.raw_url)

        self._parse_headers(http_request_lines[1:])

        _LOGGER.debug("HttpRequest: %s", self)
        return len(data)

    def get_head(self):
        """Returns the request start line and all headers."""
        return self.raw_request

    def __str__(self) -> str:
        return str(dict(url=self.url, hostname=self.url.hostname,
            port=self.url.port, method=self.method))


class HttpResponse(HttpMessageBase):
    _raw_response: bytes
    http_version: str
    response_code: str
    response_text: str

    def __init__(self, reader: StreamReader):
        super().__init__(reader)

    async def read(self) -> int:
        data = await self._read_headers()
        _LOGGER.debug("HttpResponse: received %s", data)
        if len(data) == 0:
            return 0

        self._raw_response = data
        http_response_lines = data.split(CRLF)

        # Split the response (first) line
        self._start_line = http_response_lines[0].decode()
        self.http_version, self.response_code, self.response_text = self._start_line.split(" ")

        self._parse_headers(http_response_lines[1:])
        return len(data)

    def get_head(self):
        """Returns the status line and all headers."""
        if self._dirty:
            # Recalculate head (start line + headers)
            headers = [f"{k}: {v}".encode() for k, v in self._headers.items()]
            self._raw_response = (self._start_line.encode() + CRLF +
                CRLF.join(headers) + CRLF + CRLF)
            self._dirty = False
        return self._raw_response

    def __str__(self) -> str:
        return str(dict(http_version=self.http_version,
            response_code=self.response_code, response_text=self.response_text))
