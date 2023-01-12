"""XML utilities. Assumes usage of the xml.etree.ElementTree module"""

def toint(node):
    return int(node.text)

def tofloat(node):
    return float(node.text) if node.text else 0.0

def tobool(node):
    return node.text.lower() == "on"

def totext(node):
    return node.text

def findnode(root, xpath):
    """Finds an XML node, allowing for leading '/' or '.' to be used"""
    xpath = xpath[1:] if xpath.startswith("/") else xpath
    path_components = xpath.split("/")
    if path_components[0] == ".":
        return root.find(xpath)
    if path_components[0] == root.tag:
        return root.find("/".join(path_components[1:]))
    return None

def map_xml_payload(node, handler_map):
    """Converts an XML node into a dictionary based on the supplied map"""
    result = { }
    for k, v in handler_map.items():
        subNode = findnode(node, k)
        result.update({ v["name"]: v["handler"](subNode) })
    return result
