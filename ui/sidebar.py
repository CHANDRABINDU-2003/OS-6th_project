"""ui/sidebar.py - Left navigation rail.

A vertical list of the primary apps. Each row glows on hover and launches its
app on click. Reads nothing but the (label, glyph) list it is given.
"""

import tkinter as tk

from ui import colors as C
from ui import fonts as F
from ui.animations import hover


class Sidebar(tk.Frame):
    def __init__(self, parent, items, launch, width=210):
        super().__init__(parent, bg=C.nav(), width=width)
        self.pack_propagate(False)
        self.launch = launch

        tk.Label(self, text="Navigator", font=F.h2(), fg=C.muted(),
                 bg=C.nav()).pack(anchor="w", padx=20, pady=(20, 10))

        for label, glyph in items:
            self._nav_row(label, glyph)

        tk.Frame(self, bg=C.nav()).pack(fill="both", expand=True)
        tk.Label(self, text="MiniOS X  ·  v2.0", font=F.small(),
                 fg=C.muted(), bg=C.nav()).pack(side="bottom", pady=14)

    def _nav_row(self, label, glyph):
        row = tk.Frame(self, bg=C.nav(), cursor="hand2")
        row.pack(fill="x", padx=12, pady=3)
        bar = tk.Frame(row, bg=C.nav(), width=3)
        bar.pack(side="left", fill="y")
        icon = tk.Label(row, text=glyph, font=F.ui(15), bg=C.nav(),
                        fg=C.text(), width=2)
        icon.pack(side="left", padx=(8, 6), pady=8)
        text = tk.Label(row, text=label, font=F.ui(11, "bold"), bg=C.nav(),
                        fg=C.muted())
        text.pack(side="left")

        def enter():
            row.config(bg=C.card()); bar.config(bg=C.accent())
            icon.config(bg=C.card(), fg=C.blue())
            text.config(bg=C.card(), fg=C.text())

        def leave():
            for w in (row, bar, icon, text):
                w.config(bg=C.nav())
            bar.config(bg=C.nav())
            icon.config(fg=C.text()); text.config(fg=C.muted())

        for w in (row, bar, icon, text):
            w.bind("<Button-1>", lambda _e, n=label: self.launch(n))
            hover(w, enter, leave)
