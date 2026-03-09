"""
Helpers for locating ffmpeg in source and bundled builds.
"""

import os
import shutil
import subprocess
from pathlib import Path

from core.runtime import get_runtime_root


def _binary_name(name: str) -> str:
    return f"{name}.exe" if os.name == "nt" else name


def _runtime_candidates() -> list[Path]:
    runtime_root = get_runtime_root()
    binary_name = _binary_name("ffmpeg")
    return [
        runtime_root / binary_name,
        runtime_root / "ffmpeg" / binary_name,
        runtime_root / "vendor" / "ffmpeg" / binary_name,
    ]


def _common_ffmpeg_paths() -> list[Path]:
    if os.name == "nt":
        program_files = [
            os.environ.get("ProgramFiles", ""),
            os.environ.get("ProgramFiles(x86)", ""),
            os.environ.get("LocalAppData", ""),
        ]
        candidates = [
            Path(base) / "ffmpeg" / "bin" / "ffmpeg.exe"
            for base in program_files
            if base
        ]
        candidates.extend(
            [
                Path.home() / "scoop" / "shims" / "ffmpeg.exe",
                Path.home() / "AppData" / "Local" / "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe",
            ]
        )
        chocolatey_root = os.environ.get("ChocolateyInstall", "")
        if chocolatey_root:
            candidates.extend(
                [
                    Path(chocolatey_root) / "lib" / "ffmpeg" / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe",
                    Path(chocolatey_root) / "lib" / "ffmpeg-full" / "tools" / "ffmpeg" / "bin" / "ffmpeg.exe",
                ]
            )
        return candidates

    return [
        Path("/opt/homebrew/bin/ffmpeg"),
        Path("/usr/local/bin/ffmpeg"),
        Path("/opt/local/bin/ffmpeg"),
    ]


def find_ffmpeg() -> str | None:
    """Return an absolute path to ffmpeg when available."""
    candidates: list[Path] = []

    env_path = os.environ.get("FFMPEG_PATH", "").strip()
    if env_path:
        expanded = Path(env_path).expanduser()
        if expanded.is_dir():
            candidates.append(expanded / _binary_name("ffmpeg"))
        else:
            candidates.append(expanded)

    candidates.extend(_runtime_candidates())

    which_path = shutil.which(_binary_name("ffmpeg")) or shutil.which("ffmpeg")
    if which_path:
        candidates.append(Path(which_path))

    candidates.extend(_common_ffmpeg_paths())

    for candidate in candidates:
        expanded = candidate.expanduser()
        if expanded.is_file() and os.access(expanded, os.X_OK) and is_working_ffmpeg(expanded):
            return str(expanded)

    return None


def is_working_ffmpeg(path: Path | str) -> bool:
    """Return True when the binary is executable and responds as ffmpeg."""
    try:
        result = subprocess.run(
            [str(path), "-version"],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
    except OSError:
        return False
    except subprocess.SubprocessError:
        return False

    output = f"{result.stdout}\n{result.stderr}".lower()
    return result.returncode == 0 and "ffmpeg version" in output


def ensure_ffmpeg_in_path() -> str | None:
    """Add ffmpeg's directory to PATH for subprocesses and return the binary path."""
    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        return None

    ffmpeg_dir = str(Path(ffmpeg_path).parent)
    path_parts = os.environ.get("PATH", "").split(os.pathsep) if os.environ.get("PATH") else []
    if ffmpeg_dir not in path_parts:
        os.environ["PATH"] = os.pathsep.join([ffmpeg_dir, *path_parts]) if path_parts else ffmpeg_dir

    return ffmpeg_path
