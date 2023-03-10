"""
Python HTTPS proxy server with asyncio streams
(based on the work found at https://gist.github.com/2minchul/609255051b7ffcde023be93572b25101)
"""

import asyncio
from asyncio.streams import StreamReader, StreamWriter
from contextlib import closing
from dataclasses import dataclass, asdict
import logging
import ipaddress
from typing import Any, Optional, Tuple

import async_timeout

from .callback import ProxyServerAction, ProxyServerCallback
from .httprequest import HttpRequest, HttpResponse
from .stream import StreamPair

BUFFER_SIZE = 16 * 1024
LOOPBACK_NETWORK = ipaddress.ip_network("127.0.0.0/8")

_LOGGER = logging.getLogger(__name__)

@dataclass
class HttpServerOptions:
    allow_loopback_target: bool = False


class HttpServer:
    def __init__(self, address: str, port: int):
        self._proxy_address = address
        self._proxy_port = port
        self._server: asyncio.Server
        self._callback: Optional[ProxyServerCallback] = None
        self._options = HttpServerOptions()


    def register_callback(self, callback: ProxyServerCallback) -> None:
        self._callback = callback


    def set_options(self, **kwargs: Any) -> None:
        for option, value in kwargs.items():
            if option not in asdict(self._options):
                raise ValueError(f"invalid option '{option}'")
            _LOGGER.info("HttpServerOption %s set to %s", option, value)
            setattr(self._options, option, value)


    async def close(self) -> None:
        if self._server:
            self._server.close()
            await self._server.wait_closed()


    async def pipe_stream(
        self, reader: StreamReader, writer: StreamWriter, n: int = -1, prefix: str = ""
        ) -> None:

        bytes_left = 0
        if n > 0:
            bytes_left = n
            bytes_to_read = min(BUFFER_SIZE, bytes_left)
            _LOGGER.debug("pipe_stream(%s): reading %d bytes", prefix, bytes_left)
        else:
            bytes_to_read = BUFFER_SIZE
            _LOGGER.debug("pipe_stream(%s): reading until EOF", prefix)

        while not reader.at_eof():
            data = await reader.read(bytes_to_read)
            bytes_read = len(data)
            _LOGGER.debug("pipe_stream(%s): read(%d) = %d",
                prefix, bytes_to_read, bytes_read)
            if prefix:
                _LOGGER.debug("pipe_stream(%s): %s", prefix, data.__repr__())
            writer.write(data)
            await writer.drain()

            if n > 0:
                bytes_left -= bytes_read
                _LOGGER.debug("pipe_stream(%s): bytes left: %d bytes", prefix, bytes_left)
                if bytes_left == 0:
                    break
                bytes_to_read = min(BUFFER_SIZE, bytes_left)


    async def connect_streams(
        self, local_stream: StreamPair, remote_stream: StreamPair) -> None:

        local_reader, local_writer = local_stream
        remote_reader, remote_writer = remote_stream

        tasks = (
            asyncio.create_task(
                self.pipe_stream(local_reader, remote_writer, prefix="=>"),
                name="LocalToRemotePipe"),
            asyncio.create_task(
                self.pipe_stream(remote_reader, local_writer, prefix="<="),
                name="RemoteToLocalPipe")
            )
        _, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            _LOGGER.debug("cancelling task %s", task.get_name())
            task.cancel()


    def get_proxy_target(self, request: HttpRequest) -> Tuple[str, int]:
        if request.url.hostname:
            _LOGGER.debug("get_proxy_target: using hostname/port from url")
            hostname = request.url.hostname
            port = request.url.port or 80
        else:
            host = request.headers["Host"] if "Host" in request.headers else None
            if not host:
                raise RuntimeError("missing target from both url and host header")

            _LOGGER.debug("get_proxy_target: falling back to Host header to determine server")
            if ":" in host:
                hostname, port_number = host.split(":")
                port = int(port_number)
            else:
                hostname = host
                port = 80
            _LOGGER.debug("get_proxy_target: hostname=%s; port=%d", hostname, port)

        return hostname, port


    def is_loopback(self, address: str) -> bool:
        if address == "localhost":
            return True

        try:
            ip = ipaddress.ip_address(address)
            return ip in LOOPBACK_NETWORK
        except ValueError:
            return False


    async def http_handler(
        self,
        addr: Tuple[str, int],
        client_reader: StreamReader,
        client_writer: StreamWriter) -> None:

        target_hostname = None
        target_port = None
        server_writer = None
        while True:
            # Read request from client
            request = HttpRequest(addr, client_reader)
            bytes_read = await request.read_headers()
            if bytes_read == 0:
                break

            if request.method == 'CONNECT':  # https
                await self.https_handler(client_reader, client_writer, request)
                break

            # Evaluate if we need to connect to a new target
            new_hostname, new_port = self.get_proxy_target(request)
            if (not self._options.allow_loopback_target
                and self.is_loopback(new_hostname)):

                _LOGGER.error("cannot have loopback as a proxy target")
                break

            if target_hostname != new_hostname and target_port != new_port:
                target_hostname = new_hostname
                target_port = new_port
                if server_writer:
                    server_writer.close()
                    await server_writer.wait_closed()

                _LOGGER.debug("connecting to %s:%d...", target_hostname,
                    target_port)
                server_reader, server_writer = await asyncio.open_connection(
                    target_hostname, target_port)
                _LOGGER.debug("HTTP connection established to %s:%d",
                    target_hostname, target_port)

            # assert(server_reader is not None)
            assert server_writer is not None

            _LOGGER.debug(">>> request phase >>>")
            proxy_action = ProxyServerAction.Forward
            if self._callback:
                proxy_action = await self._callback.on_new_request_async(request)
                _LOGGER.debug("proxy action: %s", proxy_action.name)

            if proxy_action == ProxyServerAction.Forward:
                # Send the request line and headers to the server unaltered
                head = request.get_head()
                _LOGGER.debug("sending to server: %s", head)
                server_writer.write(head)
                await server_writer.drain()

                # For requests that have a body, send the body next
                request_length = request.get_content_length()
                if request_length > 0:
                    await self.pipe_stream(request.get_streamreader(),
                        server_writer, request_length, prefix="=>")

            #
            # Read server response
            #

            _LOGGER.debug("<<< response phase <<<")

            # It only really makes sense to read a response from the server if
            # we forwarded the request up to the server in the first place. If
            # we have suppressed the request, the only option we have is to give
            # the callback an opportunity to provide one.
            if proxy_action == ProxyServerAction.Forward:
                response = HttpResponse(server_reader)
                await response.read()
            else:
                response = HttpResponse()

            if self._callback:
                await self._callback.on_new_response_async(
                    proxy_action, request, response)

            # If weCheck if the callback provided a proper response. If nothing
            # was provided, respond with 500 Internal Error back to the client.
            if not response.is_valid():
                _LOGGER.error("invalid response from callback. "
                    "Sending internal error (500) to client.")

                response.http_version = request.version
                response.response_code = 500
                response.response_text = "Internal Error"
                response.set_body("""
                <html>
                    <title>Internal Application Error</title>
                    <body>
                        <h1>pyProxy Application Error</h1>
                        <p>The application callback did not provide a valid HTTP
                        response after suppressing a request.</p>
                    </body>
                </html>""".encode())

            # Send the response line and headers back to the client unaltered
            head = response.get_head()
            _LOGGER.debug("sending to client: %s", head)
            client_writer.write(head)
            await client_writer.drain()

            # For responses that have a body, send the body next
            response_length = response.get_content_length()
            if response_length > 0:
                await self.pipe_stream(response.get_streamreader(),
                    client_writer, response_length, prefix="<=")

        if server_writer:
            server_writer.close()
            await server_writer.wait_closed()

        _LOGGER.debug("http_handler: done")


    async def https_handler(
        self, reader: StreamReader, writer: StreamWriter, request: HttpRequest) -> None:

        remote_reader, remote_writer = await asyncio.open_connection(
            request.url.hostname, request.url.port)
        with closing(remote_writer):
            writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            await writer.drain()
            _LOGGER.debug("HTTPS connection established")

            await self.connect_streams((reader, writer), (remote_reader, remote_writer))


    async def connection_handler(self, reader: StreamReader, writer: StreamWriter) -> None:
        async def session() -> None:
            addr = writer.get_extra_info('peername')
            _LOGGER.debug("connection from %s", addr.__repr__())

            try:
                async with async_timeout.timeout(30):
                    with closing(writer):
                        await self.http_handler(addr, reader, writer)
            except asyncio.IncompleteReadError as e:
                _LOGGER.debug("incomplete read: expected %dbytes, got %d bytes",
                    e.expected, len(e.partial))
            except asyncio.TimeoutError:
                _LOGGER.debug("timeout")

            _LOGGER.debug("connection closed")

        asyncio.create_task(session(), name="session")


    async def run(self) -> None:
        self._server = await asyncio.start_server(
            self.connection_handler, self._proxy_address, self._proxy_port)
        addr = self._server.sockets[0].getsockname()
        _LOGGER.debug("serving on %s", addr)

        async with self._server:
            await self._server.serve_forever()
