"""
Python HTTPS proxy server with asyncio streams
(based on the work found at https://gist.github.com/2minchul/609255051b7ffcde023be93572b25101)
"""

import asyncio
import async_timeout
from asyncio.streams import StreamReader, StreamWriter
from contextlib import closing
from typing import Tuple

from proxy.httprequest import HttpRequest

StreamPair = Tuple[StreamReader, StreamWriter]

BUFFER_SIZE = 1024

class MultiWriterStream(StreamWriter):
    def __init__(self, *writers):
        self.writers = writers

    def write(self, data):
        for writer in self.writers:
            writer.write(data)

    # def writelines(self, data):
    #     for writer in self.writers:
    #         writer.writelines(data)

    # def write_eof(self):
    #     for writer in self.writers:
    #         writer.write_eof(data)
    #     return self._transport.write_eof()

    # def can_write_eof(self):
    #     return self._transport.can_write_eof()

    def close(self):
        for writer in self.writers:
            writer.close()

    async def drain(self):
        drain_awaitables = [writer.drain() for writer in self.writers]
        await asyncio.gather(*drain_awaitables)


class RequestHandler:
    def __init__(self, address, port, wsserver):
        self._proxy_address = address
        self._proxy_port = port
        self._wsserver = wsserver

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


    async def pipe_stream(self, reader: StreamReader, writer: StreamWriter, prefix=None):
        try:
            while not reader.at_eof():
                data = await reader.read(BUFFER_SIZE)
                if prefix:
                    print(f"Proxy: {prefix} {data.decode()!r}", end=None)
                writer.write(data)
                await writer.drain()
        finally:
            writer.close()

    async def relay_streams(
        self, local_stream: StreamPair, remote_stream: StreamPair):

        local_reader, local_writer = local_stream
        remote_reader, remote_writer = remote_stream

        tasks = (
            asyncio.create_task(
                self.pipe_stream(local_reader, remote_writer, "=>"),
                name="LocalToRemotePipe"),
            asyncio.create_task(
                self.pipe_stream(remote_reader, local_writer, "<="),
                name="RemoteToLocalPipe")
            )
        _, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            print(f"Proxy: cancelling task {task.get_name()}")
            task.cancel()

    async def http_handler(
        self, reader: StreamReader, writer: StreamWriter, request: HttpRequest):

        if request.url:
            hostname = request.url.hostname or self._forward_to_host
            port = request.url.port or self._forward_to_port
        else:
            hostname = self._forward_to_host
            port = self._forward_to_port

        host = request.headers["Host"]
        ws_incoming, ws_outgoing = self._wsserver.get_streams(host)

        remote_reader, remote_writer = await asyncio.open_connection(hostname, port)
        if ws_incoming and ws_outgoing:
            writer = MultiWriterStream(writer, ws_incoming)
            remote_writer = MultiWriterStream(remote_writer, ws_outgoing)

        with closing(remote_writer):
            print(f"Proxy: HTTP connection established to {hostname}:{port}")
            # Send all the request data read so far first
            remote_writer.write(request.raw_request)
            await remote_writer.drain()

            await self.relay_streams((reader, writer), (remote_reader, remote_writer))


    async def https_handler(
        self, reader: StreamReader, writer: StreamWriter, request: HttpRequest):

        remote_reader, remote_writer = await asyncio.open_connection(
            request.url.hostname, request.url.port)
        with closing(remote_writer):
            writer.write(b'HTTP/1.1 200 Connection Established\r\n\r\n')
            await writer.drain()
            print("Proxy: HTTPS connection established")

            await self.relay_streams((reader, writer), (remote_reader, remote_writer))


    async def main_handler(self, reader: StreamReader, writer: StreamWriter):
        async def session():
            addr = writer.get_extra_info('peername')
            print(f"Proxy: connection from {addr!r}")

            try:
                async with async_timeout.timeout(30):
                    with closing(writer):
                        data = await reader.readuntil(b"\r\n\r\n")
                        print(f"Proxy: received {data}")

                        request = HttpRequest(data)
                        print(f"Proxy: request: {str(request)}")

                        if request.method in ("GET", "POST", "DELETE", "PUT", "HEAD"):
                            await self.http_handler(reader, writer, request)
                        elif request.method == 'CONNECT':  # https
                            await self.https_handler(reader, writer, request)
                        else:
                            print(f"Proxy: {request.method} method is not supported")
            except asyncio.IncompleteReadError:
                print("Incomplete read")
            except asyncio.TimeoutError:
                print("Timeout")

            print("Proxy: closed connection")

        asyncio.create_task(session(), name="session")


    def forward_to(self, host, port=80):
        self._forward_to_host = host
        self._forward_to_port = port


    async def run(self):
        server = await asyncio.start_server(
            self.main_handler, self._proxy_address, self._proxy_port)
        addr = server.sockets[0].getsockname()
        print(f"Proxy: serving on {addr}")

        async with server:
            await server.serve_forever()
