import asyncio
from urllib.parse import urlparse
from aiohttp.streams import StreamReader
from .stream import MemoryStreamReader

class HttpRequest:
    def __init__(self, addr, reader: StreamReader):
        self._reader = reader
        self.clientip, self.clientport = addr
        self.raw_request = None
        self.method = None
        self.raw_url = None
        self.version = None
        self.url = None
        self.headers = { }
        self.body = b""
        print(f"HttpRequest: clientip={self.clientip}, clientport={self.clientport}")

    async def _read_headers(self):
        try:
            # Read the request line and all the request headers
            return await self._reader.readuntil(b"\r\n\r\n")
        except asyncio.IncompleteReadError as e:
            return e.partial

    async def read_headers(self):
        data = await self._read_headers()
        print(f"HttpRequest: received {data}")
        if len(data) == 0:
            return 0

        self.raw_request = data
        http_request_lines = data.split(b"\r\n")

        # Split the request (first) line
        request_line = http_request_lines[0].decode()
        self.method, self.raw_url, self.version = request_line.split(" ")
        self.url = urlparse(self.raw_url)

        body_index = 1
        self.headers = { }
        for line in http_request_lines[1:]:
            if not line:
                break
            name, value = line.decode().split(": ")
            self.headers[name] = value
            body_index += 1

        # self.body = b"".join(http_request_lines[body_index + 1:])

        print(f"HttpRequest: {self}")
        return len(data)

    def __str__(self):
        return str(dict(url=self.url, hostname=self.url.hostname, port=self.url.port,
            method=self.method))

    def get_streamreader(self):
        if self.body:
            return MemoryStreamReader(self.body)
        else:
            return self._reader

    def get_request_length(self):
        return int(self.headers["Content-Length"]
            if "Content-Length" in self.headers else -1)

    async def read_body(self):
        if not self.body:
            self.body = await self._reader.readexactly(self.get_request_length())
        return self.body


class HttpResponse:
    def __init__(self, reader: StreamReader):
        self._reader = reader
        self.raw_response = None
        self.http_version = None
        self.response_code = None
        self.response_text = None
        self.headers = { }

    async def read(self):
        # Read the response line and all the response headers
        data = await self._reader.readuntil(b"\r\n\r\n")
        print(f"HttpResponse: received {data}")

        self.raw_response = data
        http_response_lines = data.split(b"\r\n")

        # Split the response (first) line
        response_line = http_response_lines[0].decode()
        self.http_version, self.response_code, self.response_text = response_line.split(" ")

        body_index = 1
        self.headers = { }
        for line in http_response_lines[1:]:
            if not line:
                break
            name, value = line.decode().split(": ")
            self.headers[name] = value
            body_index += 1

    def __str__(self):
        return str(dict(http_version=self.http_version,
            response_code=self.response_code, response_text=self.response_text))

    def get_streamreader(self):
        return self._reader

    def get_response_length(self):
        return int(self.headers["Content-Length"]
            if "Content-Length" in self.headers else -1)

    async def read_body(self):
        return self._reader.read(self.get_response_length())
