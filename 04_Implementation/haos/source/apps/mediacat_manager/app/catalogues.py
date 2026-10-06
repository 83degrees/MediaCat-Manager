"""Catalogue discovery, editing, validation, history, diff and restore workflow."""

from __future__ import annotations

import difflib
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Any, Protocol

import yaml

from path_policy import FilesystemPolicy, PathPolicyError
from storage import atomic_replace_catalogue, snapshot_catalogue

MAX_CATALOGUE_BYTES = 5 * 1024 * 1024


class CatalogueError(RuntimeError):
    """Raised for a safe, user-visible catalogue workflow failure."""


class CatalogueLoader(yaml.SafeLoader):
    """Safe YAML loader that preserves scalar dates and rejects duplicate keys."""


CatalogueLoader.yaml_implicit_resolvers = deepcopy(yaml.SafeLoader.yaml_implicit_resolvers)
for resolver_key, resolvers in CatalogueLoader.yaml_implicit_resolvers.items():
    CatalogueLoader.yaml_implicit_resolvers[resolver_key] = [
        resolver for resolver in resolvers if resolver[0] != "tag:yaml.org,2002:timestamp"
    ]


def _construct_unique_mapping(loader: CatalogueLoader, node: yaml.MappingNode, deep: bool = False) -> dict[Any, Any]:
    mapping: dict[Any, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        try:
            duplicate = key in mapping
        except TypeError as error:
            raise CatalogueError("catalogue contains an invalid mapping key") from error
        if duplicate:
            raise CatalogueError(f"catalogue contains duplicate key {key!r}")
        mapping[key] = loader.construct_object(value_node, deep=deep)
    return mapping


CatalogueLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
    _construct_unique_mapping,
)


class AdminClient(Protocol):
    def capabilities(self) -> dict[str, Any]: ...
    def validate(self, catalogue_yaml: str) -> dict[str, Any]: ...
    def reload(self) -> dict[str, Any]: ...


@dataclass(frozen=True)
class DiscoveredCatalogue:
    catalogue_id: str
    relative_name: str
    document: dict[str, Any]


class CatalogueManager:
    def __init__(self, policy: FilesystemPolicy, admin: AdminClient, *, history_keep: int = 20) -> None:
        self.policy = policy
        self.admin = admin
        self.history_keep = history_keep
        self._mutation_lock = RLock()

    def discover(self) -> dict[str, Any]:
        root = self.policy.catalogue_root
        catalogues: list[dict[str, Any]] = []
        errors: list[dict[str, str]] = []
        identities: dict[str, str] = {}
        if not root.is_dir():
            return {"catalogues": [], "errors": [{"file": "", "message": "catalogue directory is unavailable"}]}
        for path in sorted((*root.rglob("*.yaml"), *root.rglob("*.yml"))):
            relative_name = path.relative_to(root).as_posix()
            try:
                safe_path = self.policy.catalogue_file(relative_name)
                document = self._load(self._read(safe_path))
                catalogue_id = self._catalogue_id(document)
                if catalogue_id in identities:
                    raise CatalogueError(f"duplicate catalogue_id also used by {identities[catalogue_id]}")
                identities[catalogue_id] = relative_name
                catalogues.append(
                    {
                        "catalogue_id": catalogue_id,
                        "relative_name": relative_name,
                        "schema_version": document.get("catalogue_schema_version"),
                        "item_count": len(document.get("items", {})) if isinstance(document.get("items"), dict) else 0,
                        "category_count": len(document.get("categories", {})) if isinstance(document.get("categories"), dict) else 0,
                    }
                )
            except (OSError, UnicodeError, yaml.YAMLError, CatalogueError) as error:
                errors.append({"file": relative_name, "message": str(error)})
        return {"catalogues": catalogues, "errors": errors}

    def get(self, catalogue_id: str) -> dict[str, Any]:
        found = self._find(catalogue_id)
        return {"catalogue_id": found.catalogue_id, "relative_name": found.relative_name, "document": found.document}

    def save(self, catalogue_id: str, document: object) -> dict[str, Any]:
        with self._mutation_lock:
            return self._save(catalogue_id, document)

    def _save(self, catalogue_id: str, document: object) -> dict[str, Any]:
        found = self._find(catalogue_id)
        candidate = self._document(document)
        if self._catalogue_id(candidate) != catalogue_id:
            raise CatalogueError("catalogue_id cannot be changed during an edit")
        candidate_yaml = self._dump(candidate)
        self.admin.capabilities()
        validation = self.admin.validate(candidate_yaml)
        if not validation.get("valid"):
            return {"saved": False, "validation": validation}
        if validation.get("catalogue_id") != catalogue_id:
            raise CatalogueError("MediaCat validation returned a different catalogue_id")

        destination = self.policy.catalogue_file(found.relative_name)
        snapshot = snapshot_catalogue(
            self.policy, catalogue_id, destination, keep=self.history_keep
        )
        atomic_replace_catalogue(self.policy, found.relative_name, candidate_yaml.encode("utf-8"))
        reload_result = self.admin.reload()
        return {
            "saved": True,
            "validation": validation,
            "reload": reload_result,
            "snapshot": snapshot.name,
            "runtime_active": bool(reload_result.get("reloaded")),
        }

    def history(self, catalogue_id: str) -> list[dict[str, Any]]:
        self._find(catalogue_id)
        directory = self.policy.history_directory(catalogue_id)
        if not directory.is_dir():
            return []
        return [
            {"snapshot": path.name, "size": path.stat().st_size}
            for path in sorted(directory.glob("*.yaml"), key=lambda value: value.name, reverse=True)
        ]

    def diff(self, catalogue_id: str, snapshot_name: str) -> dict[str, Any]:
        found = self._find(catalogue_id)
        snapshot = self._snapshot(catalogue_id, snapshot_name)
        current = self.policy.catalogue_file(found.relative_name)
        old = self._read(snapshot).splitlines(keepends=True)
        new = self._read(current).splitlines(keepends=True)
        return {
            "snapshot": snapshot.name,
            "diff": "".join(difflib.unified_diff(old, new, fromfile=snapshot.name, tofile="current")),
        }

    def restore(self, catalogue_id: str, snapshot_name: str) -> dict[str, Any]:
        with self._mutation_lock:
            return self._restore(catalogue_id, snapshot_name)

    def _restore(self, catalogue_id: str, snapshot_name: str) -> dict[str, Any]:
        found = self._find(catalogue_id)
        snapshot = self._snapshot(catalogue_id, snapshot_name)
        candidate_yaml = self._read(snapshot)
        candidate = self._load(candidate_yaml)
        if self._catalogue_id(candidate) != catalogue_id:
            raise CatalogueError("snapshot catalogue_id does not match the selected catalogue")
        self.admin.capabilities()
        validation = self.admin.validate(candidate_yaml)
        if not validation.get("valid"):
            return {"restored": False, "validation": validation}
        current = self.policy.catalogue_file(found.relative_name)
        preserved = snapshot_catalogue(
            self.policy, catalogue_id, current, keep=self.history_keep
        )
        atomic_replace_catalogue(self.policy, found.relative_name, candidate_yaml.encode("utf-8"))
        reload_result = self.admin.reload()
        return {
            "restored": True,
            "validation": validation,
            "reload": reload_result,
            "snapshot": preserved.name,
            "runtime_active": bool(reload_result.get("reloaded")),
        }

    def _find(self, catalogue_id: str) -> DiscoveredCatalogue:
        matches: list[DiscoveredCatalogue] = []
        root = self.policy.catalogue_root
        if root.is_dir():
            for path in sorted((*root.rglob("*.yaml"), *root.rglob("*.yml"))):
                try:
                    relative_name = path.relative_to(root).as_posix()
                    safe_path = self.policy.catalogue_file(relative_name)
                    document = self._load(self._read(safe_path))
                    if self._catalogue_id(document) == catalogue_id:
                        matches.append(
                            DiscoveredCatalogue(catalogue_id, relative_name, document)
                        )
                except (OSError, UnicodeError, yaml.YAMLError, CatalogueError, PathPolicyError):
                    continue
        if not matches:
            raise CatalogueError("catalogue was not found")
        if len(matches) > 1:
            raise CatalogueError("duplicate catalogue_id prevents safe editing")
        return matches[0]

    def _snapshot(self, catalogue_id: str, snapshot_name: str) -> Path:
        if Path(snapshot_name).name != snapshot_name or not snapshot_name.endswith(".yaml"):
            raise PathPolicyError("snapshot name is invalid")
        directory = self.policy.history_directory(catalogue_id).resolve(strict=False)
        candidate = (directory / snapshot_name).resolve(strict=False)
        try:
            candidate.relative_to(directory)
        except ValueError as error:
            raise PathPolicyError("snapshot path escapes history") from error
        if not candidate.is_file():
            raise CatalogueError("snapshot was not found")
        return candidate

    @staticmethod
    def _load(content: str) -> dict[str, Any]:
        document = yaml.load(content, Loader=CatalogueLoader)
        return CatalogueManager._document(document)

    @staticmethod
    def _read(path: Path) -> str:
        if path.stat().st_size > MAX_CATALOGUE_BYTES:
            raise CatalogueError("catalogue exceeds the supported 5 MiB limit")
        return path.read_text(encoding="utf-8")

    @staticmethod
    def _document(document: object) -> dict[str, Any]:
        if not isinstance(document, dict) or not all(isinstance(key, str) for key in document):
            raise CatalogueError("catalogue document must be a string-keyed mapping")
        CatalogueManager._require_json_safe(document)
        return document

    @staticmethod
    def _require_json_safe(value: object) -> None:
        if isinstance(value, dict):
            if not all(isinstance(key, str) for key in value):
                raise CatalogueError("catalogue mappings must use string keys")
            for nested in value.values():
                CatalogueManager._require_json_safe(nested)
            return
        if isinstance(value, list):
            for nested in value:
                CatalogueManager._require_json_safe(nested)
            return
        if value is None or isinstance(value, (str, int, float, bool)):
            return
        raise CatalogueError(f"catalogue contains unsupported YAML value {type(value).__name__}")

    @staticmethod
    def _catalogue_id(document: dict[str, Any]) -> str:
        catalogue_id = document.get("catalogue_id")
        if not isinstance(catalogue_id, str) or not catalogue_id:
            raise CatalogueError("catalogue_id is missing or invalid")
        return catalogue_id

    @staticmethod
    def _dump(document: dict[str, Any]) -> str:
        return yaml.safe_dump(document, sort_keys=False, allow_unicode=True)
