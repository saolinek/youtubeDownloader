"""
py2app setup script for YTMusic Smart Downloader.
Builds a native macOS .app bundle for Apple Silicon.

Usage:
    pip install py2app
    python setup_app.py py2app
"""

from setuptools import setup

APP = ["main.py"]
APP_NAME = "YTMusic Smart Downloader"

DATA_FILES = []

OPTIONS = {
    "argv_emulation": False,
    "iconfile": "assets/icon.icns",
    "plist": {
        "CFBundleName": APP_NAME,
        "CFBundleDisplayName": APP_NAME,
        "CFBundleIdentifier": "com.ytmusic.smartdownloader",
        "CFBundleVersion": "1.0.0",
        "CFBundleShortVersionString": "1.0.0",
        "LSMinimumSystemVersion": "13.0",
        "NSHighResolutionCapable": True,
        "CFBundleDevelopmentRegion": "English",
        "NSHumanReadableCopyright": "YTMusic Smart Downloader — Privacy First",
        "LSApplicationCategoryType": "public.app-category.music",
    },
    "packages": [
        "customtkinter",
        "yt_dlp",
        "PIL",
        "certifi",
        "mutagen",
    ],
    "includes": [
        "core",
        "core.config",
        "core.downloader",
        "core.ffmpeg",
        "gui",
        "gui.main_window",
        "gui.download_panel",
        "gui.settings_dialog",
        "gui.theme",
    ],
    "excludes": [
        "tkinter.test",
        "unittest",
        "pytest",
    ],
    "resources": [],
    "strip": True,
    "semi_standalone": False,
}

setup(
    name=APP_NAME,
    app=APP,
    data_files=DATA_FILES,
    options={"py2app": OPTIONS},
    setup_requires=["py2app"],
)
