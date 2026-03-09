"""
Settings Dialog — Material 3 Light Design.
"""

import customtkinter as ctk
from core.config import Config

from gui.theme import M3


class SettingsDialog(ctk.CTkToplevel):
    def __init__(self, parent, config: Config):
        super().__init__(parent)
        self.config = config
        self.title("⚙️ Settings")
        self.geometry("520x520")
        self.configure(fg_color=M3["bg"])
        self.transient(parent)
        self.grab_set()
        self._build()
        self.after(100, self.lift)

    def _card(self, parent):
        return ctk.CTkFrame(parent, corner_radius=20, fg_color=M3["surface_container_low"],
                            border_width=1, border_color=M3["outline_variant"])

    def _build(self):
        ctk.CTkLabel(self, text="⚙️ Settings", font=ctk.CTkFont(size=22, weight="bold"),
                     text_color=M3["on_surface"]).pack(pady=(20, 16))

        sc = ctk.CTkScrollableFrame(self, fg_color="transparent")
        sc.pack(fill="both", expand=True, padx=20, pady=(0, 8))

        # Audio format
        c1 = self._card(sc); c1.pack(fill="x", pady=(0, 10))
        i1 = ctk.CTkFrame(c1, fg_color="transparent"); i1.pack(fill="x", padx=20, pady=14)
        ctk.CTkLabel(i1, text="🎵 Audio Format", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=M3["on_surface"]).pack(anchor="w")
        self.fmt = ctk.StringVar(value=self.config.get("audio_format", "mp3"))
        ff = ctk.CTkFrame(i1, fg_color="transparent"); ff.pack(fill="x", pady=(8,0))
        for f in ["mp3","m4a","flac","opus","wav"]:
            ctk.CTkRadioButton(ff, text=f.upper(), variable=self.fmt, value=f,
                               font=ctk.CTkFont(size=13)).pack(side="left", padx=(0,12))

        # Quality
        c2 = self._card(sc); c2.pack(fill="x", pady=(0, 10))
        i2 = ctk.CTkFrame(c2, fg_color="transparent"); i2.pack(fill="x", padx=20, pady=14)
        ctk.CTkLabel(i2, text="🎚 Audio Quality", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=M3["on_surface"]).pack(anchor="w")
        self.qual = ctk.StringVar(value=self.config.get("audio_quality", "0"))
        for label, val in [("Best 320k","0"),("High 256k","256"),("Medium 192k","192"),("Low 128k","128")]:
            ctk.CTkRadioButton(i2, text=label, variable=self.qual, value=val,
                               font=ctk.CTkFont(size=13)).pack(anchor="w", pady=2)

        # Privacy Mode
        c_priv = self._card(sc); c_priv.pack(fill="x", pady=(0, 10))
        i_priv = ctk.CTkFrame(c_priv, fg_color="transparent"); i_priv.pack(fill="x", padx=20, pady=14)
        ctk.CTkLabel(i_priv, text="🔒 Privacy Mode", font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=M3["on_surface"]).pack(anchor="w")
        self.priv_mode = ctk.StringVar(value=self.config.get("privacy_mode", "anonymous"))
        fp = ctk.CTkFrame(i_priv, fg_color="transparent"); fp.pack(fill="x", pady=(8,0))
        ctk.CTkRadioButton(fp, text="Anonymous (No Login)", variable=self.priv_mode, value="anonymous",
                           font=ctk.CTkFont(size=13)).pack(anchor="w", pady=2)
        ctk.CTkRadioButton(fp, text="Cookies File (cookies.txt)", variable=self.priv_mode, value="cookies",
                           font=ctk.CTkFont(size=13)).pack(anchor="w", pady=2)

        # Rate limiting
        c3 = self._card(sc); c3.pack(fill="x", pady=(0, 10))
        i3 = ctk.CTkFrame(c3, fg_color="transparent"); i3.pack(fill="x", padx=20, pady=14)
        ctk.CTkLabel(i3, text="⏱ Rate Limit (sec between tracks)",
                     font=ctk.CTkFont(size=14, weight="bold"),
                     text_color=M3["on_surface"]).pack(anchor="w")
        sf = ctk.CTkFrame(i3, fg_color="transparent"); sf.pack(fill="x", pady=(8,0))
        ctk.CTkLabel(sf, text="Min:", text_color=M3["on_surface_var"]).pack(side="left")
        self.rmin = ctk.CTkSlider(sf, from_=1, to=15, number_of_steps=14, width=120)
        self.rmin.set(self.config.get("rate_limit_min", 1)); self.rmin.pack(side="left", padx=5)
        self.rmin_l = ctk.CTkLabel(sf, text=f"{int(self.rmin.get())}s", text_color=M3["primary"])
        self.rmin_l.pack(side="left")
        ctk.CTkLabel(sf, text="  Max:", text_color=M3["on_surface_var"]).pack(side="left")
        self.rmax = ctk.CTkSlider(sf, from_=1, to=20, number_of_steps=19, width=120)
        self.rmax.set(self.config.get("rate_limit_max", 1)); self.rmax.pack(side="left", padx=5)
        self.rmax_l = ctk.CTkLabel(sf, text=f"{int(self.rmax.get())}s", text_color=M3["primary"])
        self.rmax_l.pack(side="left")
        self.rmin.configure(command=lambda v: self.rmin_l.configure(text=f"{int(v)}s"))
        self.rmax.configure(command=lambda v: self.rmax_l.configure(text=f"{int(v)}s"))

        # Notifications
        c4 = self._card(sc); c4.pack(fill="x", pady=(0, 10))
        i4 = ctk.CTkFrame(c4, fg_color="transparent"); i4.pack(fill="x", padx=20, pady=14)
        self.notif = ctk.CTkSwitch(i4, text="🔔 Desktop notifications on completion",
                                   font=ctk.CTkFont(size=13))
        self.notif.pack(anchor="w")
        if self.config.get("notifications_enabled", True): self.notif.select()

        # Buttons
        bf = ctk.CTkFrame(self, fg_color="transparent"); bf.pack(fill="x", padx=20, pady=(4,16))
        ctk.CTkButton(bf, text="💾 Save", command=self._save,
                      font=ctk.CTkFont(size=14, weight="bold"), height=42, corner_radius=21,
                      fg_color=M3["primary"], text_color=M3["on_primary"]
                      ).pack(side="left", fill="x", expand=True)
        ctk.CTkButton(bf, text="Cancel", command=self.destroy,
                      height=42, width=90, corner_radius=21,
                      fg_color=M3["secondary_container"], text_color=M3["secondary"]
                      ).pack(side="left", padx=(10,0))

    def _save(self):
        new_data = {
            "privacy_mode": self.priv_mode.get(),
            "audio_format": self.fmt.get(),
            "audio_quality": self.qual.get(),
            "rate_limit_min": int(self.rmin.get()),
            "rate_limit_max": int(self.rmax.get()),
            "notifications_enabled": bool(self.notif.get()),
        }
        for k, v in new_data.items():
            self.config._data[k] = v
        self.config.save()
        self.destroy()
