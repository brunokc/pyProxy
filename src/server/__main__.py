import asyncio

from .server import RequestHandler

if __name__ == "__main__":
    handler = RequestHandler()
    try:
        asyncio.run(handler.run())
    except KeyboardInterrupt:
        print("Exiting.")
