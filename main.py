#!/usr/bin/env python3
"""
YTMusic Smart Downloader — Privacy-First YouTube Music Downloader

A beautiful macOS desktop application for downloading YouTube Music playlists
with maximum privacy protection.

Usage:
    python main.py
"""

import sys
import os

# Ensure the project root is in path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.config import Config
from gui.main_window import MainWindow


def main():
    """Launch the YTMusic Smart Downloader application."""
    # Initialize configuration
    config = Config()

    # Create and run the main window
    app = MainWindow(config)
    app.mainloop()


if __name__ == "__main__":
    main()
