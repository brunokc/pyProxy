from urllib.parse import urlparse

CRLF = b'\r\n'

class HttpRequest:
    def __init__(self, raw_request: bytes):
        self.raw_request = raw_request
        http_request_lines = raw_request.split(CRLF)

        # Split the request (first) line
        request_line = http_request_lines[0].decode()
        self.method, self.raw_url, self.version = request_line.split(' ')
        self.url = urlparse(self.raw_url)

        body_index = 1
        self.headers = { }
        for line in http_request_lines[1:]:
            if not line:
                break
            name, value = line.decode().split(': ')
            self.headers[name] = value
            body_index += 1

        self.body = b"".join(http_request_lines[body_index + 1:])

    def __str__(self):
        return str(dict(url=self.url, hostname=self.url.hostname, port=self.url.port,
            method=self.method))
