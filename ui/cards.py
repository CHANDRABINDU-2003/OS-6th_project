"""ui/cards.py - Modern application cards for the dashboard.

Each app becomes a glass card: a big glyph, its title, a one-line subtitle of the
concepts it demonstrates, and a Launch button. Hovering glows the border and
lifts the surface; clicking anywhere on the card launches the app.
"""

import tkinter as tk

from ui import colors as C
from ui import fonts as F
from ui.widgets import GlassPanel, GlowButton
from ui.animations import hover


class AppCard(GlassPanel):
    def __init__(self, parent, name, glyph, subtitle, launch, accent=None):
        super().__init__(parent, pad=0)
        self.name = name
        self._launch = launch
        self._accent = accent or C.accent()

        wrap = tk.Frame(self.body, bg=C.card())
        wrap.pack(fill="both", expand=True, padx=16, pady=14)

        icon = tk.Label(wrap, text=glyph, font=F.ui(30), bg=C.card(),
                        fg=self._accent)
        icon.pack(anchor="w")
        title = tk.Label(wrap, text=name, font=F.h1(), fg=C.text(),
                         bg=C.card())
        title.pack(anchor="w", pady=(8, 2))
        sub = tk.Label(wrap, text=subtitle, font=F.small(), fg=C.muted(),
                       bg=C.card(), justify="left", wraplength=170)
        sub.pack(anchor="w")

        btn = GlowButton(wrap, "Launch  ›", lambda: launch(name), kind="ghost")
        btn.pack(anchor="w", pady=(12, 0))

        # Hover: whole card reacts and is clickable.
        for w in (wrap, icon, title, sub):
            w.bind("<Button-1>", lambda _e: launch(name))
            w.config(cursor="hand2")
        hover(self, self._enter, self._leave)
        for w in (wrap, icon, title, sub):
            hover(w, self._enter, self._leave)

    def _enter(self):
        self.glow(True)
        self.config(bg=C.card_hi())

    def _leave(self):
        self.glow(False)
        self.config(bg=C.card())
