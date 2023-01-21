import asyncio
from asyncio.streams import StreamReader, StreamWriter
from typing import Tuple

StreamPair = Tuple[StreamReader, StreamWriter]

# Consider using io.BytesIO underneath
class MemoryStreamReader(StreamReader):
    def __init__(self, data):
        self._data = data
        self._read_index = 0

    def close(self):
        pass

    async def read(self, n=-1):
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

# class MultiWriterStream(StreamWriter):
#     def __init__(self, *writers):
#         self.writers = writers

#     def write(self, data):
#         for writer in self.writers:
#             writer.write(data)

#     def close(self):
#         for writer in self.writers:
#             writer.close()

#     async def drain(self):
#         drain_awaitables = [writer.drain() for writer in self.writers]
#         await asyncio.gather(*drain_awaitables)


# class MemoryStream(StreamReader, StreamWriter):
#     def __init__(self):
#         self._data = b""
#         self._read_index = 0
#         self._write_index = 0

#     def close(self):
#         pass

#     # StreamReader
#     async def read(self, n=-1):
#         data = None
#         datalen = len(self._data)
#         data_left = datalen - self._read_index
#         if data_left > 0:
#             count = n if n > 0 else datalen
#             upper_index = self._read_index + count
#             data = self._data[self._read_index:upper_index]
#             self._read_index += count
#         return data

#     def at_eof(self) -> bool:
#         return self._read_index == len(self._data) - 1

#     # StreamWriter
#     def write(self, data):
#         self._data += data
#         self._write_index += len(data)

#     async def drain(self):
#         pass


# class CallbackStreamReader(StreamReader):
#     def __init__(self, callback_context):
#         self.callback_context = callback_context
#         self.data = None
#         self.index = 0

#     async def read(self, n=-1):
#         if not self.data:
#             self.data = self.callback_context.callback.read(n)
#         if n == -1:
#             data = self.data
#             self.data = None
#             self.index = 0
#             return data
#         else:
#             length = min(len(self.data), n - self.index)
#             end = self.index + length + 1
#             data = self.data[self.index:end]
#             self.index += length
#             return data

#     def at_eof(self) -> bool:
#         return self.index == len(self.data)

#     def close(self):
#         pass


# class CallbackStreamWriter(StreamWriter):
#     def __init__(self, callback_context):
#         self.callback_context = callback_context
#         self.data = b""

#     def write(self, data):
#         # if data is None:
#         #     pass
#         self.data += data

#     def close(self):
#         pass

#     async def drain(self):
#         self.request.append_body(self.data)
#         context = self.callback_context
#         context.result = await context.callback.on_new_request_async(context.request)
#         self.data = b""
