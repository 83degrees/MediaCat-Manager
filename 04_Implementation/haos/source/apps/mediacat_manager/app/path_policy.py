"""Deny-by-default filesystem policy for MediaCat Manager."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class PathPolicyError(ValueError):
    """Raised when a requested path escapes its approved boundary."""


@dataclass(frozen=True)
class FilesystemPolicy:
    catalogue_root: Path
    asset_root: Path
    history_root: Path

    @classmethod
    def home_assistant_defaults(cls) -> "FilesystemPolicy":
        return cls(
            catalogue_root=Path("/homeassistant/mediacat/catalogues"),
            asset_root=Path("/homeassistant/www/ha-assets"),
            history_root=Path("/data/history"),
        )

    def catalogue_file(self, relative_name: str) -> Path:
        candidate = self._confined(self.catalogue_root, relative_name)
        if candidate.suffix.lower() not in {".yaml", ".yml"}:
            raise PathPolicyError("catalogue files must use .yaml or .yml")
        return candidate

    def asset_file(self, relative_name: str) -> Path:
        return self._confined(self.asset_root, relative_name)

    def history_directory(self, catalogue_id: str) -> Path:
        if not catalogue_id or any(
            character not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
            for character in catalogue_id
        ):
            raise PathPolicyError("catalogue_id is not safe for history storage")
        return self._confined(self.history_root, catalogue_id)

    @staticmethod
    def _confined(root: Path, relative_name: str) -> Path:
        relative = Path(relative_name)
        if not relative_name or relative.is_absolute() or ".." in relative.parts:
            raise PathPolicyError("path must be a non-empty relative path")

        resolved_root = root.resolve(strict=False)
        resolved_candidate = (resolved_root / relative).resolve(strict=False)
        try:
            resolved_candidate.relative_to(resolved_root)
        except ValueError as error:
            raise PathPolicyError("path escapes approved root") from error
        return resolved_candidate
