# import aiohttp
import asyncio
# from enum import Enum
import json
import re
import urllib.parse
import xml.etree.ElementTree as ET

import sys
sys.path.append("..")

from proxy.callback import ProxyServerAction
from proxy.proxyserver import ProxyServer, ProxyMode, ProxyServerCallback

from .zone import *

PROXY_IP = ""
PROXY_PORT = 8080

def handle_xml_response(node, handler_map):
    status = { }
    for k, v in handler_map.items():
        subNode = findnode(node, k)
        status.update({ v["name"]: v["handler"](subNode) })
    return status

# async def read(stream, length):
#     bytes_to_read = length
#     data = b""
#     while bytes_to_read > 0:
#         data += await stream.read(bytes_to_read)
#         bytes_to_read -= len(data)
#     return data

class RequestHandler(ProxyServerCallback):
    def __init__(self):
        pass

    def parse_form_data(self, form_data):
        # Convert URL encoded HTML form data into a dictionary
        values = { k:urllib.parse.unquote(v) for (k,v) in
            [entry.split(b"=") for entry in form_data.split(b"&")]
        }
        return values

    async def on_new_request(self, request):
        print(f"Processing request {request.method} {request.url.path}")
        if request.method == "POST":
            for path, map in response_handler_map.items():
                match = re.match(path, request.raw_url)
                if match:
                    sn = match.group(1)
                    status = {
                        "serialNumber": sn
                    }

                    print(f"Handling POST for {path}")
                    body = await request.read_body()
                    print(f"Body ({len(body)} bytes): {body}")

                    form_data = self.parse_form_data(body)
                    payload = form_data[b"data"]
                    print(f"Payload: {payload}")

                    tree = ET.fromstring(payload)
                    status.update(handle_xml_response(tree, map))
                    print(json.dumps(status))
                    break

        return ProxyServerAction.Forward

    async def on_new_response(self, response):
        return ProxyServerAction.Forward

    async def run(self):
        server = ProxyServer(PROXY_IP, PROXY_PORT)
        server.register_callback(self, ProxyMode.Intercept)
        await server.run()
