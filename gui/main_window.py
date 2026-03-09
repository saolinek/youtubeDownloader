"""
Main Window for YTMusic Smart Downloader.
Light Material 3 (Material You) design.
"""

import platform
import customtkinter as ctk

from core.config import Config
from core.downloader import Downloader
from core.ffmpeg import ensure_ffmpeg_in_path
from core.runtime import get_resource_path


from gui.download_panel import DownloadPanel
from gui.settings_dialog import SettingsDialog

from gui.theme import M3
from tkinter import messagebox


class MainWindow(ctk.CTk):
    """Main application window — Material 3 Light."""

    APP_NAME = "YTMusic Smart Downloader"
    APP_VERSION = "1.0.0"
    WINDOW_WIDTH = 900
    WINDOW_HEIGHT = 850
    TITLE_FONT_FAMILY = {
        "Darwin": "SF Pro Display",
        "Windows": "Segoe UI",
    }.get(platform.system())

    def __init__(self, config: Config):
        super().__init__()
        self.config = config
        self.ffmpeg_path = ensure_ffmpeg_in_path()
        self.downloader = Downloader(config)

        self.title(self.APP_NAME)
        self.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self.minsize(600, 500)
        self.configure(fg_color=M3["bg"])

        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")
        self._set_icon()

        self._build_ui()
        self.after(100, self._check_ffmpeg)

    def _check_ffmpeg(self):
        if not self.ffmpeg_path:
            messagebox.showerror(
                "FFmpeg Missing",
                self._ffmpeg_help_text(),
            )

    @staticmethod
    def _ffmpeg_help_text() -> str:
        prefix = "FFmpeg is required for audio conversion but was not found on your system.\n\n"

        if platform.system() == "Windows":
            return (
                prefix
                + "Install it with winget:\nwinget install Gyan.FFmpeg\n\n"
                + "Or set FFMPEG_PATH to your ffmpeg.exe."
            )

        if platform.system() == "Darwin":
            return (
                prefix
                + "Please install it via Homebrew:\nbrew install ffmpeg\n\n"
                + "Or set FFMPEG_PATH to your ffmpeg binary."
            )

        return prefix + "Install it from your package manager, or set FFMPEG_PATH."

    def _set_icon(self):
        try:
            icon_png = get_resource_path("assets", "icon.png")
            if icon_png.exists():
                from PIL import Image, ImageTk

                img = Image.open(icon_png)
                self._window_icon = ImageTk.PhotoImage(img)
                self.iconphoto(True, self._window_icon)

            if platform.system() == "Windows":
                icon_ico = get_resource_path("assets", "icon.ico")
                if icon_ico.exists():
                    self.iconbitmap(default=str(icon_ico))
        except Exception as e:
            print(f"Could not set icon: {e}")

    def _title_font(self) -> ctk.CTkFont:
        if self.TITLE_FONT_FAMILY:
            return ctk.CTkFont(family=self.TITLE_FONT_FAMILY, size=18, weight="bold")
        return ctk.CTkFont(size=18, weight="bold")

    def _build_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=0)  # Header
        self.grid_rowconfigure(1, weight=1)  # Content

        # ── Header ────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color=M3["bg"], height=60, corner_radius=0)
        header.grid(row=0, column=0, sticky="ew", padx=20, pady=(15, 0))

        # Logo / Title
        logo_frame = ctk.CTkFrame(header, fg_color="transparent")
        logo_frame.pack(side="left", padx=5)
        
        ctk.CTkLabel(logo_frame, text="🎵", font=ctk.CTkFont(size=28)).pack(side="left")
        ctk.CTkLabel(logo_frame, text="YTMusic Smart Downloader",
                     font=self._title_font(),
                     text_color=M3["on_surface"]).pack(side="left", padx=(10, 0))

        # Settings Button (Top Right)
        ctk.CTkButton(header, text="⚙️ Settings", command=self._open_settings,
                      width=90, height=32, corner_radius=16,
                      fg_color=M3["surface_container_high"], text_color=M3["on_surface"],
                      hover_color=M3["surface_container_highest"]
                      ).pack(side="right", padx=5)

        # ── Main Content ── (Scrollable) ──────────────────────────────────
        self.content_scroll = ctk.CTkScrollableFrame(self, fg_color=M3["bg"], corner_radius=0)
        self.content_scroll.grid(row=1, column=0, sticky="nsew", padx=10, pady=(10, 10))
        
        # Instantiate unified Download Panel
        self.download_panel = DownloadPanel(self.content_scroll, self.config, self.downloader)
        self.download_panel.pack(fill="both", expand=True, padx=10)

    def _open_settings(self):
        SettingsDialog(self, self.config)
