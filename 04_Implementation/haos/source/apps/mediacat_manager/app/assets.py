"""Read-only local ha-assets discovery and delivery."""

from __future__ import annotations

import mimetypes
from pathlib import Path
from typing import Any

from path_policy import FilesystemPolicy, PathPolicyError


IMAGE_EXTENSIONS = {".avif", ".gif", ".jpeg", ".jpg", ".png", ".svg", ".webp"}
MAX_ASSET_BYTES = 20 * 1024 * 1024


class AssetBrowser:
    def __init__(self, policy: FilesystemPolicy) -> None:
        self.policy = policy

    def list(self, relative_directory: str = ".") -> dict[str, Any]:
        directory = self.policy.asset_file(relative_directory)
        if not directory.is_dir():
            raise PathPolicyError("asset directory is unavailable")
        entries: list[dict[str, Any]] = []
        for path in sorted(directory.iterdir(), key=lambda item: (not item.is_dir(), item.name.casefold())):
            if path.is_symlink():
                try:
                    path.resolve(strict=True).relative_to(self.policy.asset_root.resolve(strict=False))
                except (OSError, ValueError):
                    continue
            relative = path.relative_to(self.policy.asset_root).as_posix()
            if path.is_dir():
                entries.append({"kind": "directory", "name": path.name, "path": relative})
            elif path.is_file() and path.suffix.casefold() in IMAGE_EXTENSIONS:
                entries.append({"kind": "image", "name": path.name, "path": relative})
        current = "" if relative_directory in {"", "."} else directory.relative_to(self.policy.asset_root).as_posix()
        parent = str(Path(current).parent.as_posix()) if current else None
        if parent == ".":
            parent = ""
        return {"directory": current, "parent": parent, "entries": entries}

    def open(self, relative_name: str) -> tuple[str, bytes]:
        path = self.policy.asset_file(relative_name)
        if not path.is_file() or path.suffix.casefold() not in IMAGE_EXTENSIONS:
            raise PathPolicyError("asset is not a supported image")
        if path.stat().st_size > MAX_ASSET_BYTES:
            raise PathPolicyError("asset exceeds the supported 20 MiB limit")
        mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return mime_type, path.read_bytes()
