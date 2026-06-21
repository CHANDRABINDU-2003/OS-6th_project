"""apps/clock.py - Digital Clock application."""

import time
import tkinter as tk

from utils import Theme, make_label, center_window
from core.logger import log


class ClockApp(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.title("Clock")
        self.configure(bg=Theme.BG)
        center_window(self, 360, 200)
        self.resizable(False, False)

        self.time_lbl = make_label(self, "", 40, bold=True,
                                   fg=Theme.ACCENT, bg=Theme.BG)
        self.time_lbl.pack(expand=True, pady=(24, 0))

        self.date_lbl = make_label(self, "", 13,
                                   fg=Theme.TEXT_DIM, bg=Theme.BG)
        self.date_lbl.pack(expand=True, pady=(0, 24))

        self._running = True
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._tick()

        log("Clock opened")

    def _tick(self):
        if not self._running:
            return
        self.time_lbl.config(text=time.strftime("%H:%M:%S"))
        self.date_lbl.config(text=time.strftime("%A, %d %B %Y"))
        self.after(1000, self._tick)

    def _on_close(self):
        self._running = False
        self.destroy()
