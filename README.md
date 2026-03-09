# YTMusic Smart Downloader 🎵🔒

A **privacy-first** desktop application for downloading YouTube Music playlists with maximum security and anonymity.

Built with Python 3.12, CustomTkinter, and yt-dlp. Packaged as a native macOS `.app` via py2app and as a Windows `.exe` via PyInstaller.

---

## ✨ Features

### 🔒 Privacy-First Design
- **Anonymous mode** (default) — zero cookies, no Google account linkage
- **Private Playlists mode** — uses cookies from a **burner account only**
- Big red warning popup before enabling cookies
- Optional **HTTP/SOCKS5 proxy** for IP hiding
- **1 second rate limiting** between tracks by default (configurable)

### 📋 Playlist Management
- Watch multiple YouTube Music playlists (public or private)
- Auto-download **only new tracks** via `--download-archive`
- Per-playlist subfolders
- Track count and last sync timestamps

### ⬇️ Smart Downloading
- Real-time progress bar with per-track status
- Cancel mid-download safely
- macOS notifications on completion
- Configurable audio format (MP3, M4A, FLAC, OPUS, WAV) and quality

### 📖 Built-in Privacy Guide
- How to create a burner Google account
- How to export cookies from Safari & Chrome
- Privacy best practices

---

## 🚀 Quick Start

### Prerequisites

- **macOS** Ventura 13+ or **Windows 10/11**
- **Python 3.12+**
- **ffmpeg** (for audio conversion when running from source)

```bash
# macOS
brew install ffmpeg

# Windows
winget install Gyan.FFmpeg
```

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/ytmusic-smart-downloader.git
cd "YouTube downloader"

# Create a virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Launch the app
python main.py
```

### Build Native .app Bundle

```bash
pip install py2app
python setup_app.py py2app
```

The `.app` bundle will be in the `dist/` folder.

### Build Windows `.exe`

Run this on Windows:

```powershell
python -m pip install -r requirements.txt
python -m pip install pyinstaller
.\distr\windows\build_windows.ps1
```

The Windows executable is written to `distr/YTMusic Smart Downloader.exe`.

If you push to `main`, GitHub Actions also builds the Windows executable and commits it back into `distr/`.

For end users on Windows, a short launch guide is included in `distr/windows/JAK-SPUSTIT_WINDOWS.txt`.

---

## 📖 Usage Guide

### 1. Anonymous Mode (Default — Safest)

1. Launch the app — it starts in **Anonymous Mode** ✅
2. Go to **Playlists** → paste a **public** YouTube Music playlist URL
3. Click **Add** → the app fetches playlist metadata
4. Go to **Downloads** → click **Sync All Playlists**
5. Music downloads to `~/Music/YTMusic Downloads/` by default

### 2. Private Playlists Mode (Burner Account)

> ⚠️ **Only use a secondary/burner Google account!**

1. Go to **Privacy** panel
2. Toggle **Private Playlists Mode** ON
3. Read the privacy warning carefully → click OK
4. Click **Select cookies.txt File** → choose your exported cookies
5. The status shows the detected burner email
6. Now you can add **private/unlisted** playlists

### 3. Setting Up a Burner Account

1. Open an **Incognito/Private** browser window
2. Go to [accounts.google.com/signup](https://accounts.google.com/signup)
3. Create an account with a **non-personal** name and new email
4. Log into [music.youtube.com](https://music.youtube.com)
5. Export cookies (see below)

### 4. Exporting Cookies

**Chrome:**
1. Install [Get cookies.txt LOCALLY](https://chrome.google.com/webstore) extension
2. Navigate to music.youtube.com while logged into burner account
3. Click extension → Export → Save as `cookies.txt`

**Safari:**
1. Install a cookies export extension from the Mac App Store
2. Or use command line: `yt-dlp --cookies-from-browser safari --cookies cookies.txt "https://music.youtube.com"`

---

## 🗂 Project Structure

```
YouTube downloader/
├── main.py                  # Application entry point
├── requirements.txt         # Python dependencies
├── setup_app.py            # py2app packaging config
├── README.md               # This file
├── core/
│   ├── __init__.py
│   ├── config.py           # Settings persistence (JSON)
│   ├── privacy.py          # Privacy controls & validation
│   ├── downloader.py       # Threaded yt-dlp engine
│   └── playlist_manager.py # Playlist CRUD operations
└── gui/
    ├── __init__.py
    ├── main_window.py      # Root window with sidebar
    ├── privacy_panel.py    # Privacy toggles & status
    ├── playlist_panel.py   # Playlist management UI
    ├── download_panel.py   # Progress & controls
    ├── guide_dialog.py     # In-app privacy guide
    └── settings_dialog.py  # Audio/rate/notification settings
```

---

## ⚙️ Configuration

Settings are stored in `~/.ytmusic_downloader/config.json`:

| Setting | Default | Description |
|---------|---------|-------------|
| `download_folder` | `~/Music/YTMusic Downloads` | Where tracks are saved |
| `privacy_mode` | `anonymous` | `anonymous` or `cookies` |
| `audio_format` | `mp3` | `mp3`, `m4a`, `flac`, `opus`, `wav` |
| `audio_quality` | `0` (best) | Bitrate setting |
| `rate_limit_min` | `1` | Min seconds between tracks |
| `rate_limit_max` | `1` | Max seconds between tracks |
| `proxy` | `""` | Optional proxy URL |

Per-playlist download archives are stored in `~/.ytmusic_downloader/archives/`.

---

## 🔐 Privacy FAQ

**Q: Can YouTube see my downloads?**
A: In anonymous mode, YouTube sees an IP address downloading public tracks — nothing more. Use a proxy to hide your IP too.

**Q: Is my main Google account safe?**
A: Yes! Anonymous mode uses zero cookies. Cookies mode only uses your burner account's cookies. Your main account is never touched.

**Q: What if my burner account gets flagged?**
A: Simply create a new one. Your main account is unaffected.

**Q: Do cookies expire?**
A: Yes, typically after 30–90 days. Re-export when private downloads stop working.

---

## 📝 License

MIT License — use freely, but respect YouTube's Terms of Service.
This tool is intended for personal use with content you have the right to download.
