from collections import namedtuple
from typing import List, NamedTuple, Callable

from . import status, idustatus, odustatus

# ResponseHandler = namedtuple("ResponseHandler", ["method", "path", "handler"])
class ResponseHandler(NamedTuple):
    method: str
    path: str
    handler_map: dict

response_handlers: List[ResponseHandler] = [
    ResponseHandler("POST", "/systems/([^/]+)/status", status.handler_map),
    ResponseHandler("POST", "/systems/([^/]+)/idu_status", idustatus.handler_map),
    ResponseHandler("POST", "/systems/([^/]+)/odu_status", odustatus.handler_map),
]
