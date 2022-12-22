import asyncio
from asyncio.streams import StreamReader, StreamWriter
from typing import Tuple

StreamPair = Tuple[StreamReader, StreamWriter]

class MultiWriterStream(StreamWriter):
    def __init__(self, *writers):
        self.writers = writers

    def write(self, data):
        for writer in self.writers:
            writer.write(data)

    def close(self):
        for writer in self.writers:
            writer.close()

    async def drain(self):
        drain_awaitables = [writer.drain() for writer in self.writers]
        await asyncio.gather(*drain_awaitables)
