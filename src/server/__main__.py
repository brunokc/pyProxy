import asyncio
import logging

from .requesthandler import ConnexRequestHandler

PROXY_IP = ""
PROXY_PORT = 8080

_LOGGER = logging.getLogger(__name__)

def setup_logging():
    logging.basicConfig(level=logging.DEBUG, format="%(name)s: %(message)s")
    _LOGGER.setLevel(logging.DEBUG)

    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(logging.DEBUG)

    # formatter = logging.Formatter("%(name)s:%(levelname)s: %(message)s")
    # ch.setFormatter(formatter)

    _LOGGER.addHandler(ch)


if __name__ == "__main__":
    setup_logging()
    handler = ConnexRequestHandler(PROXY_IP, PROXY_PORT)
    try:
        asyncio.run(handler.run())
    except KeyboardInterrupt:
        print("Exiting.")
