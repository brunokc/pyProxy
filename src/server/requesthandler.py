import json
import logging
import re
import urllib.parse
import xml.etree.ElementTree as ET

import sys
sys.path.append("..")

from proxy.callback import ProxyServerCallback, ProxyServerAction
from proxy.proxyserver import ProxyServer

from .handlermaps import handlers, util

_LOGGER = logging.getLogger(__name__)

# async def read(stream, length):
#     bytes_to_read = length
#     data = b""
#     while bytes_to_read > 0:
#         data += await stream.read(bytes_to_read)
#         bytes_to_read -= len(data)
#     return data

class ConnexRequestHandler(ProxyServerCallback):
    def __init__(self, proxy_ip: str, proxy_port: int):
        self.proxy_ip = proxy_ip
        self.proxy_port = proxy_port

    """Convert URL encoded HTML form data into a dictionary"""
    def parse_form_data(self, form_data):
        values = { k:urllib.parse.unquote(v) for (k,v) in
            [entry.split(b"=") for entry in form_data.split(b"&")]
        }
        return values

    async def on_new_request(self, request):
        _LOGGER.debug("new request verb=%s path=%s", request.method, request.url.path)
        for handler in handlers.response_handlers:
            if request.method == handler.method:
                match = re.match(handler.path, request.raw_url)
                if match:
                    sn = match.group(1)
                    status = {
                        "serialNumber": sn
                    }

                    _LOGGER.debug("handling %s for %s", handler.method, handler.path)
                    body = await request.read_body()
                    _LOGGER.debug("body (%d bytes): %s", len(body), body)

                    form_data = self.parse_form_data(body)
                    payload = form_data[b"data"]
                    _LOGGER.debug("payload: %s", payload)

                    tree = ET.fromstring(payload)
                    status.update(util.map_xml_payload(tree, handler.handler_map))
                    _LOGGER.debug("state: %s", json.dumps(status))
                    break

        return ProxyServerAction.Forward

    async def on_new_response(self, response):
        return ProxyServerAction.Forward

    async def run(self):
        server = ProxyServer(self.proxy_ip, self.proxy_port)
        server.register_callback(self)
        await server.run()
