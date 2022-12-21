import aiohttp
import asyncio
from enum import Enum
from httprequest import HttpRequest
import json
import re
import urllib.parse
import xml.etree.ElementTree as ET

def getint(node):
    return int(node.text)

def getfloat(node):
    return float(node.text) if node.text else 0.0

def getbool(node):
    return node.text.lower() == "on"

def gettext(node):
    return node.text

zone_info_handler_map = {
    # <name>ZONE 1</name>
    # <enabled>on</enabled>
    # <currentActivity>manual</currentActivity>
    # <rt>67.0</rt>
    # <rh>34</rh>
    # <fan>off</fan>
    # <htsp>66.0</htsp>
    # <clsp>70.0</clsp>
    # <hold>on</hold>
    # <otmr/>
    # <zoneconditioning>idle</zoneconditioning>
    # <damperposition>15</damperposition>
    "./name": {
        "name": "name",
        "handler": gettext
    },
    "./enabled": {
        "name": "enabled",
        "handler": getbool
    },
    "./currentActivity": {
        "name": "currentActivity",
        "handler": gettext
    },
    "./rt": {
        "name": "temperature",
        "handler": getfloat
    },
    "./rh": {
        "name": "humidity",
        "handler": getint
    },
    "./fan": {
        "name": "fanOn",
        "handler": getbool
    },
    "./htsp": {
        "name": "heatSetpoint",
        "handler": getfloat
    },
    "./clsp": {
        "name": "coolSetpoint",
        "handler": getfloat
    },
    "./hold": {
        "name": "hold",
        "handler": getbool
    },
    "./zoneconditioning": {
        "name": "zoneConditioning",
        "handler": gettext
    }
}

def handle_zones(node):
    zones = []
    for zoneNode in node:
        zone = {
            "id": zoneNode.get("id")
        }
        zone.update(handle_zone(zoneNode))
        zones.append(zone)
    return zones

def handle_zone(node):
    status = { }
    for k, v in zone_info_handler_map.items():
        subNode = findnode(node, k)
        name = v["name"]
        handler = v["handler"]
        status.update({ name: handler(subNode) })
    return status

status_handler_map = {
    "/status/mode": {
        "name": "mode",
        "handler": gettext
    },
    "/status/cfgtype": {
        "name": "configType",
        "handler": gettext
    },
    "/status/oat": {
        "name": "outsideAirTemperature",
        "handler": getint
    },
    "/status/cfgem": {
        "name": "temperatureUnit",
        "handler": gettext
    },
    "/status/filtrlvl": {
        "name": "filterUsageLevel",
        "handler": getint
    },
    "/status/zones": {
        "name": "zones",
        "handler": handle_zones
    },
}

# POST /systems/1117W005762/idu_status
# <idu_status version="1.7">
#     <idutype>furnace2stg</idutype>
#     <pwmblower>off</pwmblower>
#     <opstat>off</opstat>
#     <iducfm>0</iducfm>
#     <blwrpm>0</blwrpm>
#     <statpress>0.00</statpress>
#     <coiltemp>na</coiltemp>
#     <inducerrpm>na</inducerrpm>
#     <lat>na</lat>
#     <lockoutactive>off</lockoutactive>
#     <lockouttime>off</lockouttime>
# </idu_status>
idu_status_handler_map = {
    "/idu_status/idutype": {
        "name": "indoorUnitType",
        "handler": gettext
    },
    "/idu_status/pwmblower": {
        "name": "?pwmBlower",
        "handler": gettext
    },
    "/idu_status/iducfm": {
        "name": "indoorUnitCFM",
        "handler": getint
    },
    "/idu_status/blwrpm": {
        "name": "blowerRPM",
        "handler": getint
    },
    "/idu_status/statpress": {
        "name": "staticPressure",
        "handler": getfloat
    },
    "/idu_status/coiltemp": {
        "name": "coilTemperature",
        "handler": getint
    },
}

# POST /systems/1117W005762/odu_status
# <odu_status version="1.7">
#     <odutype>proteushp</odutype>
#     <opstat>off</opstat>
#     <opmode>off</opmode>
#     <iducfm>0</iducfm>
#     <lat>na</lat>
#     <oducoiltmp>27</oducoiltmp>
#     <blwrpm>0</blwrpm>
#     <oat>27</oat>
#     <linevolt>237</linevolt>
#     <lockactive>off</lockactive>
#     <locktime>0</locktime>
#     <comprpm>0</comprpm>
#     <suctpress>91</suctpress>
#     <sucttemp>27</sucttemp>
#     <suctsupheat>0.0</suctsupheat>
#     <dischargetmp>92</dischargetmp>
#     <sparesensorstatus>sensor_status_invalid</sparesensorstatus>
#     <sparesensorvalue>na</sparesensorvalue>
#     <exvpos>0</exvpos>
#     <curtail>off</curtail>
#     <statpress>0.00</statpress>
#     <enterreftmp>0.00</enterreftmp>
#     <availminheatstage>2</availminheatstage>
#     <availmaxheatstage>5</availmaxheatstage>
#     <availmincoolstage>0</availmincoolstage>
#     <availmaxcoolstage>0</availmaxcoolstage>
#     <opminheatstage>2</opminheatstage>
#     <opmaxheatstage>5</opmaxheatstage>
#     <opmincoolstage>0</opmincoolstage>
#     <opmaxcoolstage>0</opmaxcoolstage>
# </odu_status>
odu_status_handler_map = {
    "/odu_status/odutype": {
        "name": "outdoorUnitType",
        "handler": gettext
    },
    "/odu_status/opmode": {
        "name": "mode",
        "handler": gettext
    },
    "/odu_status/iducfm": {
        "name": "inDoorUnitCFM",
        "handler": getint
    },
    "/odu_status/oducoiltmp": {
        "name": "coilTemperature",
        "handler": getint
    },
    "/odu_status/blwrpm": {
        "name": "blowerRPM",
        "handler": getint
    },
    "/odu_status/linevolt": {
        "name": "lineVoltage",
        "handler": getint
    },
    "/odu_status/dischargetmp": {
        "name": "dischargeTemperature",
        "handler": getint
    },
    "/odu_status/statpress": {
        "name": "staticPressure",
        "handler": getfloat
    },
}

def handle_xml_response(node, handler_map):
    status = { }
    for k, v in handler_map.items():
        subNode = findnode(node, k)
        status.update({ v["name"]: v["handler"](subNode) })
    return status

def findnode(root, xpath):
    xpath = xpath[1:] if xpath.startswith("/") else xpath
    path_components = xpath.split("/")
    if path_components[0] == ".":
        return root.find(xpath)
    if path_components[0] == root.tag:
        return root.find("/".join(path_components[1:]))
    return None

class StreamDirection(Enum):
    Outgoing = 1,
    Incoming = 2

response_handler_map = {
    "/systems/([^/]+)/status": status_handler_map,
    "/systems/([^/]+)/idu_status": idu_status_handler_map,
    "/systems/([^/]+)/odu_status": odu_status_handler_map,
}

class RequestHandler:
    def __init__(self):
        self.current_direction = None
        self.raw_request = b""
        self.raw_response = b""

    def parse_form_data(self, form_data):
        # Convert URL encoded HTML form data into a dictionary
        values = { k:urllib.parse.unquote(v) for (k,v) in
            [entry.split(b"=") for entry in form_data.split(b"&")]
        }
        return values

    def handle_request(self, data: bytes):
        if data:
            if data.startswith(b">\r\n"):
                self.current_direction = StreamDirection.Outgoing
                data = data[3:]
            elif data.startswith(b"<\r\n"):
                self.current_direction = StreamDirection.Incoming
                data = data[3:]

            # print(f">>> binary data direction: {self.current_direction}")
            # print(data)

            if self.current_direction == StreamDirection.Outgoing:
                self.raw_request += data
            else:
                self.raw_response += data
            return

        request = HttpRequest(self.raw_request)
        print(f"Processing request {request.method} {request.url.path}")
        if request.method == "POST":
            for path, map in response_handler_map.items():
                match = re.match(path, request.raw_url)
                if match:
                    sn = match.group(1)
                    status = {
                        "serialNumber": sn
                    }

                    # print(f"Body: {request.body}")
                    form_data = self.parse_form_data(request.body)
                    payload = form_data[b"data"]
                    print(f"Payload: {payload}")

                    tree = ET.fromstring(payload)
                    status.update(handle_xml_response(tree, map))
                    print(json.dumps(status))
                    break

        self.raw_request = b""
        self.raw_response = b""
        self.current_direction = None

    async def run(self):
        async with aiohttp.ClientSession() as session:
            url = "http://192.168.1.182:8787/ws"
            async with session.ws_connect(url) as ws:
                print(f"Connected to {url}")
                cmd = {
                    "command": "listen",
                    "args": {
                        "host": "www.api.eng.bryant.com"
                    }
                }
                await ws.send_json(cmd)

                print("Waiting for messages...")
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        if msg.data == 'close cmd':
                            await ws.close()
                            break
                        else:
                            print(f"Server: {msg.data}")
                    elif msg.type == aiohttp.WSMsgType.BINARY:
                        self.handle_request(msg.data)
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        break


if __name__ == "__main__":
    handler = RequestHandler()
    asyncio.run(handler.run())
