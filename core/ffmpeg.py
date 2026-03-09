"""
Helpers for locating ffmpeg in Finder-launched macOS apps.
"""

import os
import shutil
from pathlib import Path


COMMON_FFMPEG_PATHS = (
    Path("/opt/homebrew/bin/ffmpeg"),
    Path("/usr/local/bin/ffmpeg"),
    Path("/opt/local/bin/ffmpeg"),
)


def find_ffmpeg() -> str | None:
    """Return an absolute path to ffmpeg when available."""
    candidates: list[Path] = []

    env_path = os.environ.get("FFMPEG_PATH", "").strip()
    if env_path:
        candidates.append(Path(env_path).expanduser())

    which_path = shutil.which("ffmpeg")
    if which_path:
        candidates.append(Path(which_path))

    candidates.extend(COMMON_FFMPEG_PATHS)

    for candidate in candidates:
        expanded = candidate.expanduser()
        if expanded.is_file() and os.access(expanded, os.X_OK):
            return str(expanded)

    return None


def ensure_ffmpeg_in_path() -> str | None:
    """Add ffmpeg's directory to PATH for subprocesses and return the binary path."""
    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        return None

    ffmpeg_dir = str(Path(ffmpeg_path).parent)
    path_parts = os.environ.get("PATH", "").split(":") if os.environ.get("PATH") else []
    if ffmpeg_dir not in path_parts:
        os.environ["PATH"] = ":".join([ffmpeg_dir, *path_parts]) if path_parts else ffmpeg_dir

    return ffmpeg_path
