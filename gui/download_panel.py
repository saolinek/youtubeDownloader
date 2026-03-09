"""
Download Panel — Material 3 Light Design.
Handles playlist management, downloading, and progress display.
"""

import time
import threading
import customtkinter as ctk
from tkinter import filedialog

from core.config import Config
from core.downloader import Downloader, DownloadProgress

from gui.theme import M3


class DownloadPanel(ctk.CTkFrame):
    def __init__(self, parent, config: Config, downloader: Downloader):
        super().__init__(parent, fg_color=M3["bg"])
        self.config = config
        self.downloader = downloader
        self.downloader.set_callbacks(on_progress=self._on_progress, on_complete=self._on_complete)
        self._build_ui()

    def _card(self, parent, **kw):
        return ctk.CTkFrame(parent, corner_radius=20, fg_color=M3["surface_container_low"],
                            border_width=1, border_color=M3["outline_variant"], **kw)

    def _build_ui(self):
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.pack(fill="x", padx=32, pady=(10, 5))
        
        ctk.CTkLabel(header_frame, text="⬇️ Downloads",
                     font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=M3["on_surface"]).pack(side="left")

        # ── Folder Card ───────────────────────────────────────────────────
        fc = self._card(self)
        fc.pack(fill="x", padx=32, pady=(0, 10))
        fi = ctk.CTkFrame(fc, fg_color="transparent")
        fi.pack(fill="x", padx=20, pady=10)

        ctk.CTkLabel(fi, text="📁 Download Folder", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=M3["on_surface"]).pack(anchor="w")
        fr = ctk.CTkFrame(fi, fg_color="transparent")
        fr.pack(fill="x", pady=(4, 0))

        self.folder_label = ctk.CTkLabel(fr, text=self.config.download_folder,
                                          font=ctk.CTkFont(size=12),
                                          text_color=M3["tertiary"], anchor="w")
        self.folder_label.pack(side="left", fill="x", expand=True)
        ctk.CTkButton(fr, text="Change", command=self._select_folder,
                      font=ctk.CTkFont(size=11), height=28, width=70, corner_radius=14,
                      fg_color=M3["secondary_container"],
                      hover_color=M3["surface_container_high"],
                      text_color=M3["secondary"]).pack(side="right")

        # ── Playlist Management ──────────────────────────────────────────
        pc = self._card(self)
        pc.pack(fill="x", padx=32, pady=(0, 10))
        pi = ctk.CTkFrame(pc, fg_color="transparent")
        pi.pack(fill="x", padx=20, pady=12)

        # Add Playlist Input
        input_frame = ctk.CTkFrame(pi, fg_color="transparent")
        input_frame.pack(fill="x", pady=(0, 10))
        
        self.url_entry = ctk.CTkEntry(input_frame, placeholder_text="Paste YouTube Playlist URL here...",
                                      height=36, font=ctk.CTkFont(size=12), border_width=1)
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        
        self.add_btn = ctk.CTkButton(input_frame, text="Add", command=self._add_playlist, width=60, height=36,
                      fg_color=M3["primary"], text_color=M3["on_primary"])
        self.add_btn.pack(side="left")

        # Status label for adding
        self.add_status = ctk.CTkLabel(pi, text="", font=ctk.CTkFont(size=11),
                                        text_color=M3["on_surface_var"])
        self.add_status.pack(anchor="w")

        # Playlist List
        ctk.CTkLabel(pi, text="📋 Monitored Playlists", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=M3["on_surface"]).pack(anchor="w", pady=(2, 2))

        self.playlist_frame = ctk.CTkScrollableFrame(pi, height=120, fg_color="transparent")
        self.playlist_frame.pack(fill="x")
        self._refresh_playlists()

        # Action Buttons
        bf = ctk.CTkFrame(self, fg_color="transparent")
        bf.pack(fill="x", padx=32, pady=(0, 10))

        self.sync_all_btn = ctk.CTkButton(
            bf, text="🔄 Sync All Playlists", command=self._sync_all,
            font=ctk.CTkFont(size=14, weight="bold"), height=46, corner_radius=23,
            fg_color=M3["primary"], hover_color="#005A34",
            text_color=M3["on_primary"])
        self.sync_all_btn.pack(side="left", fill="x", expand=True)

        self.cancel_btn = ctk.CTkButton(
            bf, text="⛔ Cancel", command=self._cancel,
            font=ctk.CTkFont(size=12, weight="bold"), height=46, width=100, corner_radius=23,
            fg_color=M3["error_container"], hover_color="#FFB4AB",
            text_color=M3["on_error_ctr"], state="disabled")
        self.cancel_btn.pack(side="left", padx=(10, 0))

        # ── Progress Card ─────────────────────────────────────────────────
        pgc = self._card(self)
        pgc.pack(fill="x", padx=32, pady=(0, 10))
        pgi = ctk.CTkFrame(pgc, fg_color="transparent")
        pgi.pack(fill="x", padx=20, pady=12)

        self.progress_title = ctk.CTkLabel(pgi, text="Ready to download",
                                           font=ctk.CTkFont(size=13, weight="bold"),
                                           text_color=M3["on_surface"], anchor="w")
        self.progress_title.pack(anchor="w")

        self.progress_detail = ctk.CTkLabel(pgi, text="Add playlists and click 'Sync All' to start",
                                            font=ctk.CTkFont(size=11),
                                            text_color=M3["on_surface_var"], anchor="w")
        self.progress_detail.pack(anchor="w", pady=(2, 8))

        self.progress_bar = ctk.CTkProgressBar(pgi, height=6, corner_radius=3,
                                                progress_color=M3["primary"],
                                                fg_color=M3["surface_container_high"])
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)

        self.progress_pct = ctk.CTkLabel(pgi, text="0%", font=ctk.CTkFont(size=11),
                                         text_color=M3["outline"])
        self.progress_pct.pack(anchor="e", pady=(2, 0))

        # ── Log Card ──────────────────────────────────────────────────────
        lc = self._card(self)
        lc.pack(fill="both", expand=True, padx=32, pady=(0, 20))
        li = ctk.CTkFrame(lc, fg_color="transparent")
        li.pack(fill="both", expand=True, padx=20, pady=12)

        ctk.CTkLabel(li, text="📝 Activity Log", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=M3["on_surface"]).pack(anchor="w", pady=(0, 5))

        self.log_text = ctk.CTkTextbox(li, height=120, corner_radius=12,
                                        font=ctk.CTkFont(family="Menlo", size=10),
                                        fg_color=M3["surface_container"],
                                        text_color=M3["on_surface_var"],
                                        border_color=M3["outline_variant"], border_width=0)
        self.log_text.pack(fill="both", expand=True)

        self.log_text.configure(state="disabled")
        self._log("YTMusic Smart Downloader ready.")
        self._log(f"Download folder: {self.config.download_folder}")

    def _select_folder(self):
        f = filedialog.askdirectory(title="Select Download Folder",
                                    initialdir=self.config.download_folder)
        if f:
            self.config.download_folder = f
            self.folder_label.configure(text=f)
            self._log(f"Folder changed: {f}")

    def _sync_all(self):
        if not self.config.get_playlists():
            self._log("No playlists to sync!")
            return
        self.sync_all_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self._log(f"Syncing {len(self.config.get_playlists())} playlists...")
        self.downloader.sync_all_playlists()

    def sync_single(self, url, name, subfolder):
        if self.downloader.is_running:
            self._log("Download already in progress.")
            return
        self.sync_all_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self._log(f"Syncing: {name}...")
        self.downloader.download_playlist(url, name, subfolder)

    def _cancel(self):
        self.downloader.cancel()
        self.cancel_btn.configure(state="disabled")
        self._log("Cancelling...")

    def _add_playlist(self):
        """Add a playlist — fetch info in a background thread to avoid freezing the UI."""
        url = self.url_entry.get().strip()
        if not url:
            return

        # Disable add button during fetch
        self.add_btn.configure(state="disabled")
        self.add_status.configure(text="⏳ Fetching playlist info...", text_color=M3["tertiary"])

        def _fetch():
            cookies = "" if self.config.is_anonymous else self.config.cookies_file
            proxy = self.config.proxy
            info = Downloader.get_playlist_info(url, cookies, proxy)

            # Update UI on the main thread
            def _update():
                self.add_btn.configure(state="normal")
                if not info:
                    self.add_status.configure(text="⚠️ Could not fetch playlist. Check URL.", text_color=M3["error"])
                    self._log(f"⚠️ Invalid playlist URL: {url}")
                    return

                # Build playlist entry with all required fields
                import re
                folder_name = re.sub(r'[<>:"/\\|?*]', '_', info.get("title", "Playlist"))
                folder_name = folder_name.strip('. ')[:100] or "Playlist"

                playlist_data = {
                    "url": info["url"],
                    "name": info["title"],
                    "subfolder": folder_name,
                    "track_count": info.get("count", 0),
                    "count": info.get("count", 0),
                    "playlist_id": info.get("id", ""),
                    "added_at": time.strftime("%Y-%m-%d %H:%M"),
                    "last_sync": "Never",
                }

                if self.config.add_playlist(playlist_data):
                    self.url_entry.delete(0, "end")
                    self._refresh_playlists()
                    self.add_status.configure(
                        text=f"✅ Added: {info['title']} ({info.get('count', '?')} tracks)",
                        text_color=M3["primary"]
                    )
                    self._log(f"Added playlist: {info['title']} ({info.get('count', '?')} tracks)")
                else:
                    self.add_status.configure(text="⚠️ Playlist already in watchlist.", text_color=M3["error"])

            self.after(0, _update)

        threading.Thread(target=_fetch, daemon=True).start()

    def _remove_playlist(self, url):
        self.config.remove_playlist(url)
        self._refresh_playlists()
        self._log("Playlist removed.")

    def _refresh_playlists(self):
        for w in self.playlist_frame.winfo_children():
            w.destroy()
        playlists = self.config.get_playlists()

        if not playlists:
             ctk.CTkLabel(self.playlist_frame, text="No playlists added yet.",
                          text_color=M3["outline"]).pack(pady=10)
             return

        for pl in playlists:
            row = ctk.CTkFrame(self.playlist_frame, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            ctk.CTkLabel(row, text=pl.get("name", "Unknown"), font=ctk.CTkFont(weight="bold"), 
                         text_color=M3["on_surface"]).pack(side="left", padx=5)
            
            track_count = pl.get("count", pl.get("track_count", "?"))
            ctk.CTkLabel(row, text=f"({track_count} tracks)", 
                         text_color=M3["on_surface_var"]).pack(side="left", padx=5)
            
            ctk.CTkButton(row, text="❌", width=30, height=30, fg_color="transparent", 
                          text_color=M3["error"], hover_color=M3["error_container"],
                          command=lambda u=pl["url"]: self._remove_playlist(u)).pack(side="right")

    def _on_progress(self, p: DownloadProgress):
        self.after(0, lambda: self._update_ui(p))

    def _update_ui(self, p: DownloadProgress):
        labels = {
            "downloading": ("⬇️ Downloading", M3["primary"]),
            "pausing":     ("⏸ Rate limiting", M3["tertiary"]),
            "done":        ("✅ Complete", M3["primary"]),
            "error":       ("❌ Error", M3["error"]),
            "cancelled":   ("⛔ Cancelled", M3["error"]),
            "idle":        ("💤 Idle", M3["outline"]),
        }
        txt, clr = labels.get(p.status, ("...", M3["outline"]))
        if p.total_tracks:
            self.progress_title.configure(text=f"{txt} — Track {p.current_index}/{p.total_tracks}", text_color=clr)
        else:
            self.progress_title.configure(text=txt, text_color=clr)
        self.progress_detail.configure(text=p.message)

        if p.total_tracks and p.current_index:
            overall = (p.current_index - 1 + p.percent / 100) / p.total_tracks
            self.progress_bar.set(overall)
            self.progress_pct.configure(text=f"{overall * 100:.0f}%")
        elif p.percent:
            self.progress_bar.set(p.percent / 100)
            self.progress_pct.configure(text=f"{p.percent:.0f}%")

        if p.message:
            self._log(p.message)

    def _on_complete(self, ok, msg):
        def u():
            self.sync_all_btn.configure(state="normal")
            self.cancel_btn.configure(state="disabled")
            if ok:
                self.progress_bar.set(1.0)
                self.progress_pct.configure(text="100%")
            self._log(f"{'✅' if ok else '❌'} {msg}")
        self.after(0, u)

    def _log(self, msg):
        ts = time.strftime("%H:%M:%S")
        self.log_text.configure(state="normal")
        self.log_text.insert("end", f"[{ts}] {msg}\n")
        self.log_text.see("end")
        self.log_text.configure(state="disabled")
