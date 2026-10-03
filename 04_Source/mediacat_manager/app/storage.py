"""Durable catalogue and bounded-history storage primitives."""

from __future__ import annotations

import os
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from path_policy import FilesystemPolicy


def atomic_replace_catalogue(
    policy: FilesystemPolicy,
    relative_name: str,
    content: bytes,
) -> Path:
    """Atomically replace one policy-approved catalogue file.

    Validation, snapshot retention and MediaCat reload are orchestrated by the
    catalogue service before and after this narrowly scoped primitive.
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


def snapshot_catalogue(
    policy: FilesystemPolicy,
    catalogue_id: str,
    source: Path,
    *,
    keep: int = 20,
) -> Path:
    """Copy the current file into bounded Manager-owned history."""

    if keep < 1:
        raise ValueError("history retention must be at least one snapshot")
    history = policy.history_directory(catalogue_id)
    history.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    destination = history / f"{timestamp}.yaml"
    descriptor, temporary_name = tempfile.mkstemp(
        dir=history,
        prefix=f".{timestamp}.",
        suffix=".tmp",
    )
    temporary = Path(temporary_name)
    try:
        with source.open("rb") as source_handle, os.fdopen(descriptor, "wb") as handle:
            shutil.copyfileobj(source_handle, handle)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, destination)
        _sync_directory(history)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise

    snapshots = sorted(history.glob("*.yaml"), key=lambda path: path.name, reverse=True)
    for expired in snapshots[keep:]:
        expired.unlink()
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
