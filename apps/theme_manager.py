"""apps/theme_manager.py - Theme Manager.

Lets the user preview and apply one of the built-in visual themes. Applying a
theme updates the active palette (utils.Theme) and notifies subscribers (the
desktop re-themes itself; windows opened afterwards use the new colours).
"""

import tkinter as tk

from utils import Theme, THEMES, ThemeManager, make_label, make_button, center_window
from core.logger import log


class ThemeManagerApp(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.title("Theme Manager")
        self.configure(bg=Theme.BG)
        center_window(self, 460, 460)
        log("Theme Manager opened")

        make_label(self, "Theme Manager", 16, bold=True, bg=Theme.BG).pack(
            pady=(14, 4))
        make_label(self, "Pick a theme. The desktop updates instantly.",
                   10, fg=Theme.TEXT_DIM, bg=Theme.BG).pack(pady=(0, 10))

        self.holder = tk.Frame(self, bg=Theme.BG)
        self.holder.pack(fill="both", expand=True, padx=16, pady=8)
        self._build_cards()

    def _build_cards(self):
        for child in self.holder.winfo_children():
            child.destroy()

        for name, palette in THEMES.items():
            card = tk.Frame(self.holder, bg=palette["PANEL"],
                            highlightthickness=2,
                            highlightbackground=(palette["ACCENT"]
                                                 if name == Theme.name
                                                 else palette["PANEL"]))
            card.pack(fill="x", pady=6)

            top = tk.Frame(card, bg=palette["PANEL"])
            top.pack(fill="x", padx=10, pady=8)

            tk.Label(top, text=name + ("  ✓" if name == Theme.name else ""),
                     font=(Theme.FONT, 12, "bold"),
                     fg=palette["TEXT"], bg=palette["PANEL"]).pack(side="left")

            # Colour swatches
            sw = tk.Frame(top, bg=palette["PANEL"])
            sw.pack(side="left", padx=14)
            for key in ("ACCENT", "ACCENT_2", "ACCENT_3", "ACCENT_4"):
                tk.Frame(sw, bg=palette[key], width=20, height=20).pack(
                    side="left", padx=2)

            tk.Button(top, text="Apply", command=lambda n=name: self._apply(n),
                      bg=palette["ACCENT"], fg="#ffffff", relief="flat", bd=0,
                      font=(Theme.FONT, 10, "bold"), padx=12, pady=4,
                      cursor="hand2").pack(side="right")

    def _apply(self, name):
        ThemeManager.apply(name)
        log(f"Theme changed to {name}")
        self.configure(bg=Theme.BG)   # re-theme this window's shell
        self._build_cards()
