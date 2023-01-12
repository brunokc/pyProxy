from . import util

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
zone_info_handler_map = {
    "./name": {
        "name": "name",
        "handler": util.totext
    },
    "./enabled": {
        "name": "enabled",
        "handler": util.tobool
    },
    "./currentActivity": {
        "name": "currentActivity",
        "handler": util.totext
    },
    "./rt": {
        "name": "temperature",
        "handler": util.tofloat
    },
    "./rh": {
        "name": "humidity",
        "handler": util.toint
    },
    "./fan": {
        "name": "fanOn",
        "handler": util.tobool
    },
    "./htsp": {
        "name": "heatSetpoint",
        "handler": util.tofloat
    },
    "./clsp": {
        "name": "coolSetpoint",
        "handler": util.tofloat
    },
    "./hold": {
        "name": "hold",
        "handler": util.tobool
    },
    "./zoneconditioning": {
        "name": "zoneConditioning",
        "handler": util.totext
    }
}

def handle_zone(node):
    status = { }
    for k, v in zone_info_handler_map.items():
        subNode = util.findnode(node, k)
        name = v["name"]
        handler = v["handler"]
        status.update({ name: handler(subNode) })
    return status

def handle_zones(node):
    zones = []
    for zoneNode in node:
        zone = {
            "id": zoneNode.get("id")
        }
        zone.update(handle_zone(zoneNode))
        zones.append(zone)
    return zones

# Status Handler Map
# (includes zones status)
handler_map = {
    "/status/mode": {
        "name": "mode",
        "handler": util.totext
    },
    "/status/cfgtype": {
        "name": "configType",
        "handler": util.totext
    },
    "/status/oat": {
        "name": "outsideAirTemperature",
        "handler": util.toint
    },
    "/status/cfgem": {
        "name": "temperatureUnit",
        "handler": util.totext
    },
    "/status/filtrlvl": {
        "name": "filterUsageLevel",
        "handler": util.toint
    },
    "/status/zones": {
        "name": "zones",
        "handler": handle_zones
    },
}
