import aiohttp
import logging

_LOGGER = logging.getLogger(__name__)

class Requests:
    def __init__(self, proxy_ip: str, proxy_port: int):
        self._proxy_entry = { "proxy": f"http://{proxy_ip}:{proxy_port}" }

    def prepare_aiorequest(self):
        async def on_request_end(session, trace_config_ctx, params):
            _LOGGER.debug("Ending request")
            _LOGGER.debug("Request: %s %s", params.method, params.url)
            _LOGGER.debug("Headers: %s", params.headers)
            _LOGGER.debug("Headers: %s", params.response.request_info.headers)

        trace_config = aiohttp.TraceConfig()
        trace_config.on_request_end.append(on_request_end)
        return trace_config

    async def get(self, url, *args, **kargs):
        trace_config = self.prepare_aiorequest()
        async with aiohttp.ClientSession(trace_configs=[trace_config]) as session:
            kargs.update(self._proxy_entry)
            async with session.get(url, *args, **kargs) as response:
                # Ensure response is fully read before the connection is closed
                await response.read()
                return response
