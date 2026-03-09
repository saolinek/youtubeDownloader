"""
Configuration management for YTMusic Smart Downloader.
Persists settings to ~/.ytmusic_downloader/config.json
"""

import json
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_DIR = Path.home() / ".ytmusic_downloader"
DEFAULT_CONFIG_FILE = DEFAULT_CONFIG_DIR / "config.json"
DEFAULT_ARCHIVE_DIR = DEFAULT_CONFIG_DIR / "archives"

DEFAULT_CONFIG = {
    "download_folder": str(Path.home() / "Music" / "YTMusic Downloads"),
    "privacy_mode": "anonymous",  # "anonymous" or "cookies"
    "cookies_file": "",
    "proxy": "",
    "playlists": [],
    "rate_limit_min": 1,
    "rate_limit_max": 1,
    "audio_format": "mp3",
    "audio_quality": "0",  # best
    "notifications_enabled": True,
    "theme": "dark",
}


class Config:
    """Thread-safe configuration manager with JSON persistence."""

    def __init__(self, config_path: Path | None = None):
        self.config_path = config_path or DEFAULT_CONFIG_FILE
        self.config_dir = self.config_path.parent
        self.archive_dir = DEFAULT_ARCHIVE_DIR
        self._data: dict[str, Any] = {}
        self._ensure_dirs()
        self.load()

    def _ensure_dirs(self):
        """Create config and archive directories if they don't exist."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.archive_dir.mkdir(parents=True, exist_ok=True)

    def load(self):
        """Load config from disk, merging with defaults."""
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    saved = json.load(f)
                self._data = {**DEFAULT_CONFIG, **saved}
            except (json.JSONDecodeError, IOError):
                self._data = dict(DEFAULT_CONFIG)
        else:
            self._data = dict(DEFAULT_CONFIG)
        self.save()

    def save(self):
        """Persist config to disk."""
        try:
            with open(self.config_path, "w") as f:
                json.dump(self._data, f, indent=2)
        except IOError as e:
            print(f"[Config] Error saving config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def set(self, key: str, value: Any):
        self._data[key] = value
        self.save()

    def get_playlists(self) -> list[dict]:
        return self._data.get("playlists", [])

    def add_playlist(self, playlist: dict):
        playlists = self.get_playlists()
        # Avoid duplicates by URL
        if not any(p["url"] == playlist["url"] for p in playlists):
            playlists.append(playlist)
            self._data["playlists"] = playlists
            self.save()
            return True
        return False

    def remove_playlist(self, url: str):
        playlists = self.get_playlists()
        self._data["playlists"] = [p for p in playlists if p["url"] != url]
        self.save()

    def update_playlist(self, url: str, updates: dict[str, Any]) -> bool:
        """Update a tracked playlist in place."""
        playlists = self.get_playlists()
        updated = False

        for playlist in playlists:
            if playlist.get("url") == url:
                playlist.update(updates)
                updated = True
                break

        if updated:
            self._data["playlists"] = playlists
            self.save()

        return updated

    def get_archive_path(self, playlist_id: str) -> Path:
        """Return per-playlist download archive path."""
        return self.archive_dir / f"{playlist_id}.txt"

    @property
    def download_folder(self) -> str:
        return self._data.get("download_folder", DEFAULT_CONFIG["download_folder"])

    @download_folder.setter
    def download_folder(self, path: str):
        self.set("download_folder", path)

    @property
    def is_anonymous(self) -> bool:
        return self._data.get("privacy_mode") == "anonymous"

    @property
    def cookies_file(self) -> str:
        return self._data.get("cookies_file", "")

    @property
    def proxy(self) -> str:
        return self._data.get("proxy", "")
