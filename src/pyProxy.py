import asyncio

BUFFER_SIZE = 64 * 1024

PROXY_PORT = 8080
RELAY_SERVER = "www.api.eng.bryant.com"
RELAY_PORT = 80

async def pipe(reader, writer, prefix):
    try:
        while not reader.at_eof():
            data = await reader.read(BUFFER_SIZE)
            print(f"{prefix} {data.decode()!r}", end=None)
            writer.write(data)
    finally:
        writer.close()

async def handle_client(local_reader, local_writer):
    try:
        remote_reader, remote_writer = await asyncio.open_connection(RELAY_SERVER, RELAY_PORT)
        pipe1 = pipe(local_reader, remote_writer, "->")
        pipe2 = pipe(remote_reader, local_writer, "<-")
        await asyncio.gather(pipe1, pipe2)
    finally:
        local_writer.close()

async def handle_request(reader, writer):
    print(f"Opening connecting to {RELAY_SERVER}...")
    api_reader, api_writer = await asyncio.open_connection(RELAY_SERVER, RELAY_PORT)

    data = None
    while not reader.at_eof():
        data = await reader.readuntil(b'\r\n')

        print(f"-> {data.decode()!r}", end=None)

        api_writer.write(data)
        await api_writer.drain()

    api_writer.write_eof()

    data = None
    while not api_reader.at_eof():
        data = await api_reader.readuntil(b'\r\n')

        print(f"<- {data.decode()!r}", end=None)

        writer.write(data)
        await writer.drain()

    writer.write_eof()
    print("Request completed.")

async def proxy_server():
    server = await asyncio.start_server(handle_client, "0.0.0.0", PROXY_PORT)
    addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
    print(f"Serving on {addrs}")

    async with server:
        await server.serve_forever()

    server.close()

if __name__ == "__main__":
    asyncio.run(proxy_server())
