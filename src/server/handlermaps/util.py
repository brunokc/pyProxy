
def toint(node):
    return int(node.text)

def tofloat(node):
    return float(node.text) if node.text else 0.0

def tobool(node):
    return node.text.lower() == "on"

def totext(node):
    return node.text

def findnode(root, xpath):
    xpath = xpath[1:] if xpath.startswith("/") else xpath
    path_components = xpath.split("/")
    if path_components[0] == ".":
        return root.find(xpath)
    if path_components[0] == root.tag:
        return root.find("/".join(path_components[1:]))
    return None

def parse_xml_payload(node, handler_map):
    status = { }
    for k, v in handler_map.items():
        subNode = findnode(node, k)
        status.update({ v["name"]: v["handler"](subNode) })
    return status
