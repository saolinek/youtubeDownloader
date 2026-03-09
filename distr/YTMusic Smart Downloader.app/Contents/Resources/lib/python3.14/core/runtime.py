"""
Runtime helpers for bundled and source-based execution.
"""

from __future__ import annotations

import sys
from pathlib import Path


def is_frozen() -> bool:
    """Return True when the app is running from a bundled executable."""
    return bool(getattr(sys, "frozen", False))


def get_runtime_root() -> Path:
    """Return the directory that contains bundled resources."""
    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        return Path(meipass)

    if is_frozen():
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parent.parent


def get_resource_path(*parts: str) -> Path:
    """Resolve a resource path in source and bundled builds."""
    return get_runtime_root().joinpath(*parts)
