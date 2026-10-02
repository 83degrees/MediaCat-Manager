"""Catalogue storage primitives; not exposed by the ASTV-277 HTTP shell."""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

from path_policy import FilesystemPolicy


def atomic_replace_catalogue(
    policy: FilesystemPolicy,
    relative_name: str,
    content: bytes,
) -> Path:
    """Atomically replace one policy-approved catalogue file.

    Validation, snapshot retention and MediaCat reload orchestration belong to
    the ASTV-286 workflow. This primitive is deliberately unavailable through
    the bootstrap HTTP surface.
    """

    destination = policy.catalogue_file(relative_name)
    destination.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        dir=destination.parent,
        prefix=f".{destination.name}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        _sync_directory(destination.parent)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise
    return destination


def _sync_directory(directory: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    try:
        descriptor = os.open(directory, flags)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
