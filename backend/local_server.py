"""ローカル確認用の簡易 HTTP サーバー。"""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import unquote, urlparse

from app import lambda_handler

PORT = 8080


class Handler(BaseHTTPRequestHandler):
    def _handle(self) -> None:
        parsed = urlparse(self.path)
        path = unquote(parsed.path)
        event = {
            "rawPath": path,
            "requestContext": {"http": {"method": self.command}},
        }
        result = lambda_handler(event, None)
        status = int(result["statusCode"])
        headers = result.get("headers") or {}
        body = result.get("body") or ""
        self.send_response(status)
        for key, value in headers.items():
            self.send_header(key, value)
        self.end_headers()
        if body:
            self.wfile.write(body.encode("utf-8"))

    def do_GET(self) -> None:  # noqa: N802
        self._handle()

    def do_OPTIONS(self) -> None:  # noqa: N802
        self._handle()

    def log_message(self, format: str, *args) -> None:  # noqa: A003
        print("%s - %s" % (self.address_string(), format % args))


def main() -> None:
    server = HTTPServer(("127.0.0.1", PORT), Handler)
    print(json.dumps({"listening": f"http://127.0.0.1:{PORT}"}))
    server.serve_forever()


if __name__ == "__main__":
    main()
