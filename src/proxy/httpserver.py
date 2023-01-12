"""
Python HTTPS proxy server with asyncio streams
(based on the work found at https://gist.github.com/2minchul/609255051b7ffcde023be93572b25101)
"""

import asyncio
import async_timeout
from asyncio.streams import StreamReader, StreamWriter
from contextlib import closing
from enum import IntEnum
import logging

from proxy.callback import ProxyServerCallback, ProxyServerAction
from proxy.httprequest import HttpRequest, HttpResponse
from proxy.stream import StreamPair

BUFFER_SIZE = 16 * 1024

_LOGGER = logging.getLogger(__name__)


class HttpServer:
    def __init__(self, address, port, wsserver):
        self._proxy_address = address
        self._proxy_port = port
        self._wsserver = wsserver

        # Default callback that just forwards requests over to the destination
        self._callback = ProxyServerCallback()

    # async def forward_stream(self, reader: StreamReader, writer: StreamWriter, event: asyncio.Event):
    #     while not event.is_set():
    #         try:
    #             data = await asyncio.wait_for(reader.read(BUFFER_SIZE), 1)
    #         except asyncio.TimeoutError:
    #             continue

    #         if data == b'':  # when it closed
    #             event.set()
    #             break

    #         writer.write(data)
    #         await writer.drain()


    def register_callback(self, callback: ProxyServerCallback):
        self._callback = callback


    async def pipe_stream(self, reader: StreamReader, writer: StreamWriter, n=-1, prefix=None):
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
        self, local_stream: StreamPair, remote_stream: StreamPair):

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

    # async def http_handler_listenin(
    #     self,
    #     reader: StreamReader,
    #     writer: StreamWriter,
    #     request: HttpRequest):

    #     host = request.headers["Host"] if "Host" in request.headers else None

    #     if request.url.hostname:
    #         hostname = request.url.hostname # or self._forward_to_host
    #         port = request.url.port or 80 #self._forward_to_port
    #     else:
    #         if host:
    #             hostname = host
    #             port = 80

    #     # By default, we just forward the request and response along. This should
    #     # cover for the case where there's no callback registered, so it's a
    #     # safe default.
    #     proxy_action = ProxyServerAction.Forward

    #     ws_incoming, ws_outgoing = self._wsserver.get_streams(host)

    #     _LOGGER.debug("connecting to %s: %d...", hostname, port)
    #     remote_reader, remote_writer = await asyncio.open_connection(hostname, port)
    #     if ws_incoming and ws_outgoing:
    #         writer = MultiWriterStream(writer, ws_incoming)
    #         remote_writer = MultiWriterStream(remote_writer, ws_outgoing)

    #     with closing(remote_writer):
    #         _LOGGER.debug("HTTP connection established to %s:%d", hostname, port)
    #         # Send all the request data read so far first
    #         remote_writer.write(request.raw_request)
    #         await remote_writer.drain()

    #         await self.connect_streams((reader, writer), (remote_reader, remote_writer))

    def get_proxy_target(self, request):
        host = request.headers["Host"] if "Host" in request.headers else None

        if request.url.hostname:
            hostname = request.url.hostname
            port = request.url.port or 80
        else:
            if host:
                _LOGGER.debug("get_proxy_target: falling back to Host header to determine server")
                hostname = host
                port = 80

        return hostname, port

    async def http_handler(
        self,
        addr,
        client_reader: StreamReader,
        client_writer: StreamWriter):

        target_hostname = None
        target_port = None
        server_writer = None
        while True:
            request = HttpRequest(addr, client_reader)
            bytes_read = await request.read_headers()
            if bytes_read == 0:
                break

            if request.method == 'CONNECT':  # https
                await self.https_handler(client_reader, client_writer, request)
                return

            new_hostname, new_port = self.get_proxy_target(request)
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

            _LOGGER.debug("request phase")
            proxy_action = await self._callback.on_new_request(request)
            _LOGGER.debug("request proxy action: %s",
                ProxyServerAction(proxy_action).name)
            if proxy_action == ProxyServerAction.Forward:
                # Send the request line and headers to the server unaltered
                _LOGGER.debug("sending to server: %s", request.raw_request)
                server_writer.write(request.raw_request)
                await server_writer.drain()

                # For requests that have a body, send the body next
                request_length = request.get_request_length()
                if request_length > 0:
                    await self.pipe_stream(request.get_streamreader(),
                        server_writer, request_length, prefix="=>")

            # Read server response
            _LOGGER.debug("response phase")
            response = HttpResponse(server_reader)
            await response.read()
            proxy_action = await self._callback.on_new_response(response)
            _LOGGER.debug("response proxy action: %s",
                ProxyServerAction(proxy_action).name)
            if proxy_action == ProxyServerAction.Forward:
                # Send the response line and headers back to the client unaltered
                client_writer.write(response.raw_response)
                await client_writer.drain()

                # For responses that have a body, send the body next
                response_length = response.get_response_length()
                if response_length > 0:
                    await self.pipe_stream(response.get_streamreader(),
                        client_writer, response_length, prefix="<=")

        server_writer.close()
        await server_writer.wait_closed()

        _LOGGER.debug("http_handler: done")


    async def https_handler(
        self, reader: StreamReader, writer: StreamWriter, request: HttpRequest):

        remote_reader, remote_writer = await asyncio.open_connection(
            request.url.hostname, request.url.port)
        with closing(remote_writer):
            writer.write(b"HTTP/1.1 200 Connection Established\r\n\r\n")
            await writer.drain()
            _LOGGER.debug("HTTPS connection established")

            await self.connect_streams((reader, writer), (remote_reader, remote_writer))


    async def connection_handler(self, reader: StreamReader, writer: StreamWriter):
        async def session():
            addr = writer.get_extra_info('peername')
            _LOGGER.debug("connection from %s", addr.__repr__())

            try:
                async with async_timeout.timeout(30):
                    with closing(writer):
                        # request = HttpRequest(addr, reader)
                        # await request.read_headers()

                        await self.http_handler(addr, reader, writer)
                        # if request.method in ("GET", "POST", "DELETE", "PUT", "HEAD"):
                        #     await self.http_handler(addr, reader, writer)
                        # elif request.method == 'CONNECT':  # https
                        #     await self.https_handler(reader, writer, request)
                        # else:
                        #     _LOGGER.debug("%s method is not supported", request.method)
            except asyncio.IncompleteReadError as e:
                _LOGGER.debug("incomplete read: expected %dbytes, got %d bytes",
                    e.expected, len(e.partial))
                e.with_traceback()
            except asyncio.TimeoutError:
                _LOGGER.debug("timeout")

            _LOGGER.debug("closed connection")

        asyncio.create_task(session(), name="session")


    async def run(self):
        server = await asyncio.start_server(
            self.connection_handler, self._proxy_address, self._proxy_port)
        addr = server.sockets[0].getsockname()
        _LOGGER.debug("serving on %s", addr)

        async with server:
            await server.serve_forever()
