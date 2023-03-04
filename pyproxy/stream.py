from asyncio.streams import StreamReader, StreamWriter
from typing import Tuple

StreamPair = Tuple[StreamReader, StreamWriter]

# TODO: Consider using io.BytesIO underneath
class MemoryStreamReader(StreamReader):
    def __init__(self, data: bytes):
        self._data = data
        self._read_index = 0

    def close(self) -> None:
        pass

    async def read(self, n: int = -1) -> bytes:
        data = b""
        datalen = len(self._data)
        data_left = datalen - self._read_index
        if data_left > 0:
            count = n if n > 0 else datalen
            upper_index = self._read_index + count
            data = self._data[self._read_index:upper_index]
            self._read_index += count
        return data

    def at_eof(self) -> bool:
        return self._read_index == len(self._data) - 1
