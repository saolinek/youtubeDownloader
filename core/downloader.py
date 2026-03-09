"""
Threaded yt-dlp download engine for YTMusic Smart Downloader.
Handles downloading with privacy controls, rate limiting, and progress reporting.
"""

import os
import re
import random
import subprocess
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable
from urllib.parse import parse_qs, urlparse

import yt_dlp
from mutagen import File as MutagenFile

from core.config import Config
from core.ffmpeg import ensure_ffmpeg_in_path


class DownloadProgress:
    """Container for download progress information."""

    def __init__(self):
        self.current_track = ""
        self.current_index = 0
        self.total_tracks = 0
        self.percent = 0.0
        self.speed = ""
        self.eta = ""
        self.status = "idle"  # idle, downloading, pausing, done, error, cancelled
        self.message = ""


class Downloader:
    """Threaded yt-dlp wrapper with privacy-first design."""

    AUDIO_EXTENSIONS = {".mp3", ".m4a", ".flac", ".opus", ".wav", ".aac", ".ogg"}
    TRACK_ID_PATTERN = re.compile(r"(?:v=|youtu\.be/)([A-Za-z0-9_-]{6,})")

    def __init__(self, config: Config):
        self.config = config
        self.ffmpeg_path = ensure_ffmpeg_in_path()
        self._cancel_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._progress = DownloadProgress()
        self._on_progress: Callable[[DownloadProgress], None] | None = None
        self._on_complete: Callable[[bool, str], None] | None = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def progress(self) -> DownloadProgress:
        return self._progress

    def set_callbacks(
        self,
        on_progress: Callable[[DownloadProgress], None] | None = None,
        on_complete: Callable[[bool, str], None] | None = None,
    ):
        self._on_progress = on_progress
        self._on_complete = on_complete

    def _notify_progress(self):
        if self._on_progress:
            self._on_progress(self._progress)

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """Sanitize a string for use in filenames (Recordbox-safe)."""
        if not name:
            return "Unknown"
        # Remove characters that are illegal in filenames
        for ch in ['/', '\\', ':', '*', '?', '"', '<', '>', '|']:
            name = name.replace(ch, '-')
        # Collapse multiple dashes/spaces
        name = re.sub(r'-{2,}', '-', name)
        name = re.sub(r'\s{2,}', ' ', name)
        return name.strip(' .-')

    @staticmethod
    def _clean_title(title: str) -> str:
        """Remove common YouTube noise from track titles for cleaner Recordbox display."""
        if not title:
            return "Unknown"
        noise_patterns = [
            r'\s*\(Official\s*(Music\s*)?Video\)',
            r'\s*\(Official\s*Audio\)',
            r'\s*\(Lyric\s*Video\)',
            r'\s*\(Lyrics?\)',
            r'\s*\(Visualizer\)',
            r'\s*\[Official\s*(Music\s*)?Video\]',
            r'\s*\[Official\s*Audio\]',
            r'\s*\[Lyric\s*Video\]',
            r'\s*\[Lyrics?\]',
            r'\s*\[Visualizer\]',
            r'\s*【.*?】',
            r'\s*\|\s*Official\s*(Music\s*)?Video',
            r'\s*HD\s*$', r'\s*HQ\s*$', r'\s*4K\s*$', r'\s*MV\s*$',
        ]
        for pattern in noise_patterns:
            title = re.sub(pattern, '', title, flags=re.IGNORECASE)
        return title.strip()

    def _build_yt_dlp_opts(self, output_dir: str, archive_path: Path | None = None) -> dict:
        """Build yt-dlp options with privacy controls and archive support."""
        audio_format = self.config.get("audio_format", "mp3")
        
        opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": audio_format,
                    "preferredquality": self.config.get("audio_quality", "0"),
                },
                {
                    "key": "FFmpegMetadata",
                    "add_metadata": True,
                },
            ],
            "writethumbnail": False,
            "keepvideo": False,
            "outtmpl": os.path.join(output_dir, "%(artist,uploader,channel)s - %(title)s [%(id)s].%(ext)s"),
            "ignoreerrors": True,
            "no_warnings": False,
            "quiet": True,
            "progress_hooks": [self._progress_hook],
            "extract_flat": False,
            "nocheckcertificate": False,
        }

        # Use download archive if provided
        if archive_path:
            opts["download_archive"] = str(archive_path)

        if self.config.is_anonymous:
            opts["cookiefile"] = None
        else:
            cookies_file = self.config.cookies_file
            if cookies_file and Path(cookies_file).exists():
                opts["cookiefile"] = cookies_file

        proxy = self.config.proxy
        if proxy and proxy.strip():
            opts["proxy"] = proxy.strip()

        if self.ffmpeg_path:
            opts["ffmpeg_location"] = str(Path(self.ffmpeg_path).parent)

        return opts

    def _get_flat_playlist_opts(self) -> dict:
        opts = {"quiet": True, "extract_flat": True}
        if not self.config.is_anonymous and Path(self.config.cookies_file).exists():
            opts["cookiefile"] = self.config.cookies_file
        if self.config.proxy.strip():
            opts["proxy"] = self.config.proxy.strip()
        return opts

    def _progress_hook(self, d: dict):
        if d["status"] == "downloading":
            self._progress.status = "downloading"
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            downloaded = d.get("downloaded_bytes", 0)
            if total > 0:
                self._progress.percent = (downloaded / total) * 100
            self._progress.speed = d.get("_speed_str", "")
            self._progress.eta = d.get("_eta_str", "")
            self._notify_progress()
        elif d["status"] == "finished":
            self._progress.status = "downloading"
            self._progress.percent = 100
            self._progress.message = f"Converting: {Path(d.get('filename', '')).name}"
            self._notify_progress()

    def download_playlist(self, playlist_url: str, playlist_name: str, subfolder: str = ""):
        if self.is_running: return
        self._cancel_event.clear()
        self._progress = DownloadProgress()
        self._progress.status = "downloading"
        self._thread = threading.Thread(
            target=lambda: self._safe_run(self._download_playlist_logic, playlist_url, playlist_name, subfolder),
            daemon=True
        )
        self._thread.start()

    def sync_all_playlists(self):
        if self.is_running: return
        self._cancel_event.clear()
        self._progress = DownloadProgress()
        self._progress.status = "downloading"
        self._thread = threading.Thread(target=self._sync_all_worker, daemon=True)
        self._thread.start()

    def _safe_run(self, func, *args):
        try:
            result = func(*args)
        except Exception as e:
            self._progress.status = "error"
            self._progress.message = f"Error: {e}"
            self._notify_progress()
            if self._on_complete:
                self._on_complete(False, str(e))
            return

        if self._cancel_event.is_set():
            self._progress.status = "cancelled"
            if not self._progress.message:
                self._progress.message = "Sync cancelled."
            self._notify_progress()
            if self._on_complete:
                self._on_complete(False, "Cancelled")
            return

        self._progress.status = "done"
        if not self._progress.message:
            self._progress.message = "Playlist synced."
        self._notify_progress()
        if self._on_complete:
            self._on_complete(True, result or "Playlist synced")

    def _sync_all_worker(self):
        playlists = self.config.get_playlists()
        if not playlists:
            self._progress.status = "done"
            self._progress.message = "No playlists to sync."
            self._notify_progress()
            if self._on_complete: self._on_complete(True, "No playlists")
            return

        failed_playlists: list[str] = []

        for i, pl in enumerate(playlists):
            if self._cancel_event.is_set():
                break
            self._progress.message = f"Syncing {i+1}/{len(playlists)}: {pl.get('name')}"
            self._notify_progress()
            try:
                self._download_playlist_logic(pl["url"], pl.get("name"), pl.get("subfolder", ""))
            except Exception as e:
                failed_playlists.append(pl.get("name") or pl.get("url") or "Unknown playlist")
                self._progress.message = f"Error in {pl.get('name')}: {e}"
                self._notify_progress()

        if self._cancel_event.is_set():
            self._progress.status = "cancelled"
            self._progress.message = "Sync cancelled."
            self._notify_progress()
            if self._on_complete:
                self._on_complete(False, "Cancelled")
            return

        if failed_playlists:
            self._progress.status = "error"
            self._progress.message = f"Failed playlists: {', '.join(failed_playlists)}"
            self._notify_progress()
            if self._on_complete:
                self._on_complete(False, f"Failed playlists: {', '.join(failed_playlists)}")
            return

        self._progress.status = "done"
        self._progress.message = "All playlists synced!"
        self._notify_progress()
        self._send_notification("YTMusic Smart Downloader", "All playlists synced.")
        if self._on_complete:
            self._on_complete(True, "All synced")

    def _read_playlist_entries(self, playlist_url: str) -> list[dict]:
        with yt_dlp.YoutubeDL(self._get_flat_playlist_opts()) as ydl:
            info = ydl.extract_info(playlist_url, download=False)

        if not info:
            raise Exception(f"Could not fetch playlist: {playlist_url}")

        return [entry for entry in info.get("entries", []) if entry is not None]

    @classmethod
    def _extract_track_id_from_text(cls, text: str) -> str | None:
        if not text:
            return None
        match = cls.TRACK_ID_PATTERN.search(text)
        if match:
            return match.group(1)
        return None

    @classmethod
    def _frame_text_values(cls, frame) -> list[str]:
        values = getattr(frame, "text", None)
        if values:
            return [str(value) for value in values if value]
        if frame:
            return [str(frame)]
        return []

    @classmethod
    def _extract_track_id_from_file(cls, path: Path) -> str | None:
        name_match = re.search(r"\[([A-Za-z0-9_-]{6,})\](?=\.[^.]+$)", path.name)
        if name_match:
            return name_match.group(1)

        try:
            audio = MutagenFile(path)
        except Exception:
            return None

        tags = getattr(audio, "tags", None)
        if not tags:
            return None

        for key in getattr(tags, "keys", lambda: [])():
            key_text = str(key).lower()
            if "purl" not in key_text and "comment" not in key_text:
                continue
            for value in cls._frame_text_values(tags[key]):
                track_id = cls._extract_track_id_from_text(value)
                if track_id:
                    return track_id

        return None

    @classmethod
    def _read_local_track_ids(cls, output_dir: str) -> set[str]:
        local_ids: set[str] = set()
        directory = Path(output_dir)
        if not directory.exists():
            return local_ids

        for path in directory.iterdir():
            if not path.is_file() or path.suffix.lower() not in cls.AUDIO_EXTENSIONS:
                continue
            track_id = cls._extract_track_id_from_file(path)
            if track_id:
                local_ids.add(track_id)

        return local_ids

    @staticmethod
    def _read_archive_ids(archive_path: Path) -> set[str]:
        if not archive_path.exists():
            return set()

        ids: set[str] = set()
        for line in archive_path.read_text().splitlines():
            parts = line.strip().split()
            if len(parts) >= 2:
                ids.add(parts[-1])
        return ids

    @staticmethod
    def _write_archive_ids(archive_path: Path, ids: set[str]):
        archive_path.parent.mkdir(parents=True, exist_ok=True)
        lines = [f"youtube {track_id}" for track_id in sorted(ids)]
        archive_path.write_text("\n".join(lines) + ("\n" if lines else ""))

    def _sync_archive_with_library(
        self,
        archive_path: Path,
        playlist_track_ids: set[str],
        local_track_ids: set[str],
    ) -> set[str]:
        archive_ids = self._read_archive_ids(archive_path)
        preserved_ids = {track_id for track_id in archive_ids if track_id not in playlist_track_ids}
        synced_ids = preserved_ids | (local_track_ids & playlist_track_ids)

        if synced_ids != archive_ids:
            self._write_archive_ids(archive_path, synced_ids)

        return synced_ids

    @staticmethod
    def _entry_track_id(entry: dict) -> str | None:
        return entry.get("id")

    @staticmethod
    def _entry_url(entry: dict) -> str:
        return entry.get("url") or f"https://www.youtube.com/watch?v={entry['id']}"

    def _update_playlist_state(self, playlist_url: str, total_tracks: int, *, synced: bool = False):
        updates = {
            "count": total_tracks,
            "track_count": total_tracks,
        }
        if synced:
            updates["last_sync"] = datetime.now().strftime("%Y-%m-%d %H:%M")
        self.config.update_playlist(playlist_url, updates)

    def _download_playlist_logic(self, playlist_url: str, playlist_name: str, subfolder: str):
        """Download only tracks that are missing from the local playlist folder."""
        base_dir = self.config.download_folder
        output_dir = os.path.join(base_dir, subfolder or playlist_name)
        os.makedirs(output_dir, exist_ok=True)

        playlist_id = self._extract_playlist_id(playlist_url)
        archive_path = self.config.get_archive_path(playlist_id)

        entries = self._read_playlist_entries(playlist_url)
        total = len(entries)
        if total == 0:
            raise Exception(f"Playlist is empty or unavailable: {playlist_name}")

        self._progress.total_tracks = total
        self._progress.current_index = 0
        self._progress.percent = 0
        self._notify_progress()
        self._update_playlist_state(playlist_url, total)

        playlist_track_ids = {track_id for track_id in (self._entry_track_id(entry) for entry in entries) if track_id}
        local_track_ids = self._read_local_track_ids(output_dir)
        self._sync_archive_with_library(archive_path, playlist_track_ids, local_track_ids)

        missing_entries = [
            entry for entry in entries
            if (track_id := self._entry_track_id(entry)) and track_id not in local_track_ids
        ]

        if not missing_entries:
            self._progress.current_index = total
            self._progress.percent = 100
            self._progress.status = "done"
            self._progress.message = f"{playlist_name} is already up to date."
            self._notify_progress()
            self._update_playlist_state(playlist_url, total, synced=True)
            return "Playlist already up to date"

        opts = self._build_yt_dlp_opts(output_dir, archive_path)
        downloaded = 0
        failed = 0
        already_present = total - len(missing_entries)

        self._progress.message = (
            f"{playlist_name}: {already_present} already present, "
            f"{len(missing_entries)} missing."
        )
        self._notify_progress()

        for i, entry in enumerate(missing_entries, start=1):
            if self._cancel_event.is_set():
                break

            track_id = self._entry_track_id(entry)
            self._progress.current_index = already_present + i
            self._progress.current_track = entry.get("title", "Unknown")
            self._progress.percent = 0
            self._progress.status = "downloading"
            self._progress.message = f"Processing {already_present + i}/{total}: {entry.get('title')}"
            self._notify_progress()

            with yt_dlp.YoutubeDL(opts) as ydl:
                result = ydl.download([self._entry_url(entry)])
                if result == 0:
                    downloaded += 1
                    if track_id:
                        local_track_ids.add(track_id)
                else:
                    failed += 1

            if i < len(missing_entries) and not self._cancel_event.is_set():
                delay = random.uniform(self.config.get("rate_limit_min", 4), self.config.get("rate_limit_max", 8))
                self._progress.status = "pausing"
                self._progress.message = f"Waiting {delay:.1f}s..."
                self._notify_progress()
                if self._cancel_event.wait(timeout=delay):
                    break

        self._post_process_filenames(output_dir, self.config.get("audio_format", "mp3"))
        refreshed_local_ids = self._read_local_track_ids(output_dir)
        self._sync_archive_with_library(archive_path, playlist_track_ids, refreshed_local_ids)

        if self._cancel_event.is_set():
            self._progress.status = "cancelled"
            self._progress.message = f"Cancelled after downloading {downloaded} tracks."
            self._notify_progress()
            return "Cancelled"

        if failed:
            raise Exception(f"{playlist_name}: downloaded {downloaded}, failed {failed}")

        self._progress.current_index = total
        self._progress.percent = 100
        self._progress.message = f"{playlist_name}: downloaded {downloaded} missing tracks."
        self._notify_progress()
        self._update_playlist_state(playlist_url, total, synced=True)
        return f"Downloaded {downloaded} missing tracks"

    def _post_process_filenames(self, output_dir: str, ext: str):
        if not os.path.isdir(output_dir): return
        junk = {'.webm', '.webp', '.part', '.ytdl', '.temp', '.tmp'}
        audio = {'.mp3', '.m4a', '.flac', '.opus', '.wav', '.aac', '.ogg'}

        for filename in os.listdir(output_dir):
            filepath = os.path.join(output_dir, filename)
            if not os.path.isfile(filepath): continue
            _, fext = os.path.splitext(filename)
            if fext.lower() in junk:
                try: os.remove(filepath)
                except OSError: pass
                continue
            if fext.lower() not in audio: continue

            # Clean name: Artist - Title [ID] -> Artist - Title
            name = os.path.splitext(filename)[0]
            name_no_id = re.sub(r'\s*\[.*?\]$', '', name).strip()
            
            parts = name_no_id.split(' - ', 1)
            if len(parts) == 2:
                artist = self._sanitize_filename(parts[0])
                title = self._sanitize_filename(self._clean_title(parts[1]))
                base_new = f"{artist} - {title}"
            else:
                base_new = self._sanitize_filename(self._clean_title(name_no_id))

            new_name = f"{base_new}{fext}"
            new_path = os.path.join(output_dir, new_name)
            
            counter = 1
            while os.path.exists(new_path) and filename != os.path.basename(new_path):
                new_name = f"{base_new} ({counter}){fext}"
                new_path = os.path.join(output_dir, new_name)
                counter += 1

            if new_name != filename:
                try: os.rename(filepath, new_path)
                except OSError: pass

    def cancel(self):
        self._cancel_event.set()

    @staticmethod
    def _extract_playlist_id(url: str) -> str:
        import hashlib
        parsed = urlparse(url)
        params = parse_qs(parsed.query)
        pl_id = params.get("list", [None])[0]
        return pl_id if pl_id else hashlib.md5(url.encode()).hexdigest()[:16]

    def _send_notification(self, title: str, message: str):
        if not self.config.get("notifications_enabled", True):
            return
        try:
            safe_message = message.replace('"', '\\"')
            safe_title = title.replace('"', '\\"')
            subprocess.run(["osascript", "-e", f'display notification "{safe_message}" with title "{safe_title}"'],
                           capture_output=True, timeout=5)
        except Exception:
            pass

    @staticmethod
    def get_playlist_info(url: str, cookies_file: str = "", proxy: str = "") -> dict | None:
        opts = {"quiet": True, "extract_flat": True}
        if cookies_file and Path(cookies_file).exists(): opts["cookiefile"] = cookies_file
        if proxy.strip(): opts["proxy"] = proxy.strip()
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=False)
                if info:
                    return {
                        "title": info.get("title", "Unknown"),
                        "count": len([e for e in info.get("entries", []) if e is not None]),
                        "id": info.get("id", ""),
                        "url": url,
                    }
        except Exception: pass
        return None
