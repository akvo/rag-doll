import logging
from http.server import BaseHTTPRequestHandler, HTTPServer


logger = logging.getLogger(__name__)


class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok"}')
        else:
            self.send_response(404)
            self.end_headers()


def run(server_class=HTTPServer, handler_class=HealthCheckHandler, port=9001):
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    logger.info(f"Starting httpd server on port {port}")
    httpd.serve_forever()
