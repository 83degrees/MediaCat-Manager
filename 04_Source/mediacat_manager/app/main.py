"""Minimal authenticated-Ingress web shell for MediaCat Manager."""

from __future__ import annotations

import json
import os
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from path_policy import FilesystemPolicy


PRODUCT = "MediaCat Manager"
VERSION = "0.1.0"
POLICY = FilesystemPolicy.home_assistant_defaults()

INDEX = b"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>MediaCat Manager</title>
  <style>
    :root { color-scheme: light dark; font-family: system-ui, sans-serif; }
    body { margin: 0; background: #101820; color: #eef5f7; }
    main { max-width: 52rem; margin: 0 auto; padding: 3rem 1.25rem; }
    .card { background: #182832; border: 1px solid #31505e; border-radius: 1rem; padding: 1.5rem; }
    h1 { margin-top: 0; color: #7bdff2; }
    code { color: #f2b880; }
    .status { display: inline-block; border-radius: 999px; padding: .25rem .7rem; background: #174f3f; }
  </style>
</head>
<body><main><section class="card">
  <span class="status">Bootstrap ready</span>
  <h1>MediaCat Manager</h1>
  <p>The governed Home Assistant App and Ingress boundary are active.</p>
  <p>Catalogue editing, history/revert and the visual asset picker are intentionally reserved for <code>ASTV-286</code>.</p>
</section></main></body>
</html>"""


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "MediaCatManager/0.1"

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        path = self.path.split("?", 1)[0].rstrip("/") or "/"
        if path == "/":
            self._send(HTTPStatus.OK, "text/html; charset=utf-8", INDEX)
            return
        if path == "/health":
            self._json(HTTPStatus.OK, {"status": "ok", "version": VERSION})
            return
        if path == "/api/bootstrap":
            self._json(
                HTTPStatus.OK,
                {
                    "product": PRODUCT,
                    "version": VERSION,
                    "editor_available": False,
                    "mediacat_admin_interface": 1,
                    "boundaries": {
                        "catalogues": str(POLICY.catalogue_root),
                        "assets": str(POLICY.asset_root),
                        "assets_access": "read-only",
                        "history": str(POLICY.history_root),
                    },
                },
            )
            return
        self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self._json(HTTPStatus.METHOD_NOT_ALLOWED, {"error": "bootstrap_is_read_only"})

    def do_PUT(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self.do_POST()

    def do_DELETE(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self.do_POST()

    def log_message(self, format: str, *args: object) -> None:
        print(f"mediacat-manager: {format % args}", flush=True)

    def _json(self, status: HTTPStatus, payload: dict[str, object]) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self._send(status, "application/json; charset=utf-8", body)

    def _send(self, status: HTTPStatus, content_type: str, body: bytes) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'self'")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    port = int(os.environ.get("PORT", "8099"))
    server = ThreadingHTTPServer(("0.0.0.0", port), RequestHandler)
    print(f"mediacat-manager: listening on {port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
