"""ui/dock.py - macOS-style bottom dock.

A centred row of rounded icon tiles. Hovering lifts the tile a few pixels and
adds a glow; clicking launches the app. Open apps show a small indicator dot.
"""

import tkinter as tk

from ui import colors as C
from ui import fonts as F
from ui.animations import hover


class Dock(tk.Frame):
    def __init__(self, parent, items, launch, is_open=None, height=84):
        super().__init__(parent, bg=C.nav(), height=height)
        self.pack_propagate(False)
        self.launch = launch
        self.is_open = is_open or (lambda _n: False)
        self.tiles = {}

        tray = tk.Frame(self, bg=C.card(), highlightthickness=1,
                        highlightbackground=C.border())
        tray.pack(pady=12)
        for label, glyph in items:
            self._tile(tray, label, glyph)

    def _tile(self, parent, label, glyph):
        cell = tk.Frame(parent, bg=C.card())
        cell.pack(side="left", padx=7, pady=8)

        tile = tk.Label(cell, text=glyph, font=F.ui(22), width=2,
                        bg=C.card_hi(), fg=C.text(), cursor="hand2",
                        padx=6, pady=6)
        tile.pack()
        dot = tk.Label(cell, text="•", font=F.ui(12),
                       fg=C.accent() if self.is_open(label) else C.card(),
                       bg=C.card())
        dot.pack()
        self.tiles[label] = (tile, dot)

        def enter():
            tile.config(bg=C.accent(), fg="#ffffff")
            cell.pack_configure(pady=(2, 14))   # lift

        def leave():
            tile.config(bg=C.card_hi(), fg=C.text())
            cell.pack_configure(pady=8)

        tile.bind("<Button-1>", lambda _e: self.launch(label))
        hover(tile, enter, leave)

    def refresh_indicators(self):
        for label, (_tile, dot) in self.tiles.items():
            dot.config(fg=C.accent() if self.is_open(label) else C.card())
