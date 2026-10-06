"""Authenticated-Ingress HTTP application for MediaCat Manager."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, unquote, urlsplit

from admin_client import AdminClientError, MediaCatAdminClient
from assets import AssetBrowser
from catalogues import CatalogueError, CatalogueManager
from path_policy import FilesystemPolicy, PathPolicyError


PRODUCT = "MediaCat Manager"
VERSION = "0.2.0"
MAX_REQUEST_BYTES = 5 * 1024 * 1024
STATIC_ROOT = Path(__file__).with_name("static")


@dataclass(frozen=True)
class AppContext:
    policy: FilesystemPolicy
    admin: MediaCatAdminClient
    catalogues: CatalogueManager
    assets: AssetBrowser


def build_context(policy: FilesystemPolicy | None = None, admin: MediaCatAdminClient | None = None) -> AppContext:
    filesystem_policy = policy or FilesystemPolicy.home_assistant_defaults()
    admin_client = admin or MediaCatAdminClient()
    return AppContext(
        policy=filesystem_policy,
        admin=admin_client,
        catalogues=CatalogueManager(filesystem_policy, admin_client),
        assets=AssetBrowser(filesystem_policy),
    )


DEFAULT_CONTEXT = build_context()


class RequestHandler(BaseHTTPRequestHandler):
    server_version = "MediaCatManager/0.2"

    @property
    def context(self) -> AppContext:
        return getattr(self.server, "context", DEFAULT_CONTEXT)

    def do_GET(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        parsed = urlsplit(self.path)
        path = parsed.path.rstrip("/") or "/"
        try:
            if path == "/":
                self._static("index.html", "text/html; charset=utf-8")
            elif path == "/app.js":
                self._static("app.js", "text/javascript; charset=utf-8")
            elif path == "/styles.css":
                self._static("styles.css", "text/css; charset=utf-8")
            elif path == "/health":
                self._json(HTTPStatus.OK, {"status": "ok", "version": VERSION})
            elif path == "/api/bootstrap":
                self._bootstrap()
            elif path == "/api/capabilities":
                self._json(HTTPStatus.OK, self.context.admin.capabilities())
            elif path == "/api/catalogues":
                self._json(HTTPStatus.OK, self.context.catalogues.discover())
            elif path == "/api/assets":
                directory = parse_qs(parsed.query).get("directory", ["."])[0]
                self._json(HTTPStatus.OK, self.context.assets.list(directory))
            elif path == "/api/asset":
                relative_name = parse_qs(parsed.query).get("path", [""])[0]
                content_type, body = self.context.assets.open(relative_name)
                self._send(HTTPStatus.OK, content_type, body, cache="private, max-age=300")
            elif path.startswith("/api/catalogues/"):
                self._get_catalogue_route(path)
            else:
                self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
        except AdminClientError as error:
            self._json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "mediacat_unavailable", "message": str(error)})
        except (CatalogueError, PathPolicyError, OSError, UnicodeError) as error:
            self._json(HTTPStatus.BAD_REQUEST, {"error": "request_rejected", "message": str(error)})

    def do_POST(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        path = urlsplit(self.path).path.rstrip("/") or "/"
        try:
            if path.startswith("/api/catalogues/"):
                self._post_catalogue_route(path)
            else:
                self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})
        except AdminClientError as error:
            self._json(HTTPStatus.SERVICE_UNAVAILABLE, {"error": "mediacat_unavailable", "message": str(error)})
        except (CatalogueError, PathPolicyError, OSError, UnicodeError, ValueError) as error:
            self._json(HTTPStatus.BAD_REQUEST, {"error": "request_rejected", "message": str(error)})

    def do_PUT(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self._json(HTTPStatus.METHOD_NOT_ALLOWED, {"error": "method_not_allowed"})

    def do_DELETE(self) -> None:  # noqa: N802 - BaseHTTPRequestHandler API
        self.do_PUT()

    def _get_catalogue_route(self, path: str) -> None:
        parts = [unquote(part) for part in path.split("/") if part]
        if len(parts) == 3:
            self._json(HTTPStatus.OK, self.context.catalogues.get(parts[2]))
            return
        if len(parts) == 4 and parts[3] == "history":
            self._json(HTTPStatus.OK, {"history": self.context.catalogues.history(parts[2])})
            return
        if len(parts) == 6 and parts[3] == "history" and parts[5] == "diff":
            self._json(HTTPStatus.OK, self.context.catalogues.diff(parts[2], parts[4]))
            return
        self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def _post_catalogue_route(self, path: str) -> None:
        parts = [unquote(part) for part in path.split("/") if part]
        if len(parts) == 4 and parts[3] == "save":
            payload = self._read_json()
            self._json(HTTPStatus.OK, self.context.catalogues.save(parts[2], payload.get("document")))
            return
        if len(parts) == 6 and parts[3] == "history" and parts[5] == "restore":
            self._json(HTTPStatus.OK, self.context.catalogues.restore(parts[2], parts[4]))
            return
        self._json(HTTPStatus.NOT_FOUND, {"error": "not_found"})

    def _bootstrap(self) -> None:
        policy = self.context.policy
        self._json(
            HTTPStatus.OK,
            {
                "product": PRODUCT,
                "version": VERSION,
                "editor_available": True,
                "mediacat_admin_interface": 1,
                "boundaries": {
                    "catalogues": str(policy.catalogue_root),
                    "assets": str(policy.asset_root),
                    "assets_access": "read-only",
                    "history": str(policy.history_root),
                },
            },
        )

    def _read_json(self) -> dict[str, Any]:
        content_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().casefold()
        if content_type != "application/json":
            raise ValueError("Content-Type must be application/json")
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as error:
            raise ValueError("Content-Length is invalid") from error
        if length < 1 or length > MAX_REQUEST_BYTES:
            raise ValueError("request body size is invalid")
        try:
            payload = json.loads(self.rfile.read(length))
        except json.JSONDecodeError as error:
            raise ValueError("request body is not valid JSON") from error
        if not isinstance(payload, dict):
            raise ValueError("request body must be an object")
        return payload

    def _static(self, name: str, content_type: str) -> None:
        self._send(HTTPStatus.OK, content_type, (STATIC_ROOT / name).read_bytes())

    def log_message(self, format: str, *args: object) -> None:
        print(f"mediacat-manager: {format % args}", flush=True)

    def _json(self, status: HTTPStatus, payload: object) -> None:
        body = json.dumps(payload, sort_keys=True).encode("utf-8")
        self._send(status, "application/json; charset=utf-8", body)

    def _send(
        self,
        status: HTTPStatus,
        content_type: str,
        body: bytes,
        *,
        cache: str = "no-store",
    ) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", cache)
        self.send_header("Content-Security-Policy", "default-src 'self'; img-src 'self' data:; style-src 'self'; frame-ancestors 'self'")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    port = int(os.environ.get("PORT", "8099"))
    server = ThreadingHTTPServer(("0.0.0.0", port), RequestHandler)
    server.context = DEFAULT_CONTEXT  # type: ignore[attr-defined]
    print(f"mediacat-manager: listening on {port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
