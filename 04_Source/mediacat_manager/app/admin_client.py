"""Client for the provider-owned MediaCat administration actions."""

from __future__ import annotations

import json
import os
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


class AdminClientError(RuntimeError):
    """Raised when the supported MediaCat administration boundary is unavailable."""


class MediaCatAdminClient:
    """Call MediaCat through Home Assistant's response-capable service API."""

    def __init__(self, base_url: str | None = None, token: str | None = None) -> None:
        self.base_url = (base_url or os.environ.get("HOME_ASSISTANT_URL") or "http://supervisor/core").rstrip("/")
        self.token = token if token is not None else os.environ.get("SUPERVISOR_TOKEN", "")

    def capabilities(self) -> dict[str, Any]:
        response = self._call("get_admin_capabilities", {})
        if response.get("admin_interface_version") != 1:
            raise AdminClientError("MediaCat admin interface version 1 is required")
        if not response.get("validation_supported") or not response.get("transactional_reload_supported"):
            raise AdminClientError("MediaCat validation and transactional reload are required")
        if response.get("catalogue_directory") != "mediacat/catalogues":
            raise AdminClientError("MediaCat reported an unsupported catalogue directory")
        if 4 not in response.get("supported_catalogue_schema_versions", []):
            raise AdminClientError("MediaCat schema version 4 support is required")
        return response

    def validate(self, catalogue_yaml: str) -> dict[str, Any]:
        return self._call("validate_catalogue", {"catalogue_yaml": catalogue_yaml})

    def reload(self) -> dict[str, Any]:
        return self._call("reload_catalogue", {})

    def _call(self, service: str, data: dict[str, Any]) -> dict[str, Any]:
        if not self.token:
            raise AdminClientError("Home Assistant Supervisor token is unavailable")
        url = f"{self.base_url}/api/services/mediacat/{service}?return_response"
        request = Request(
            url,
            data=json.dumps(data).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with urlopen(request, timeout=20) as response:
                payload = json.load(response)
        except HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")
            raise AdminClientError(f"MediaCat action {service} failed ({error.code}): {detail}") from error
        except (URLError, TimeoutError, json.JSONDecodeError) as error:
            raise AdminClientError(f"MediaCat action {service} is unavailable: {error}") from error
        service_response = payload.get("service_response") if isinstance(payload, dict) else None
        if not isinstance(service_response, dict):
            raise AdminClientError(f"MediaCat action {service} returned no structured response")
        return service_response
