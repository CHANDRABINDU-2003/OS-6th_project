"""core/boot.py - Boot sequence (glass redesign).

A sci-fi startup screen: animated wallpaper, the MiniOS X PRO wordmark, a
staged list of subsystems coming online and a progress bar. Each step is also
written to the kernel log. Calls on_complete to hand off to login.
"""

import tkinter as tk

from ui import colors as C
from ui import fonts as F
from ui.animations import Wallpaper
from core.logger import log


BOOT_MESSAGES = [
    "Initializing kernel...",
    "Loading memory manager...",
    "Starting CPU scheduler...",
    "Mounting virtual file system...",
    "Loading device drivers...",
    "Starting system services...",
    "Loading desktop environment...",
    "Ready.",
]


class BootScreen(tk.Frame):
    def __init__(self, root, on_complete):
        super().__init__(root, bg=C.bg())
        self.root = root
        self.on_complete = on_complete
        self.pack(fill="both", expand=True)
        log("System boot started", level="BOOT")

        self.canvas = tk.Canvas(self, bg=C.bg(), highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.wallpaper = Wallpaper(self.canvas, node_count=18, star_count=30)

        # Wordmark
        self.canvas.create_text(0, 0, text="MiniOS", font=F.ui(46, "bold"),
                                fill=C.text(), tags=("brand", "mini"))
        self.canvas.create_text(0, 0, text="X PRO", font=F.ui(46, "bold"),
                                fill=C.accent(), tags=("brand", "pro"))
        self.canvas.create_text(0, 0, text="Operating System Simulator  ·  Version 2.0",
                                font=F.body(), fill=C.muted(), tags="brand")

        self.status = tk.Label(self.canvas, text="", font=F.ui(10),
                               fg=C.muted(), bg=C.bg())
        self.bar_w = 440
        self.bar = tk.Canvas(self.canvas, width=self.bar_w, height=4,
                             bg=C.track(), highlightthickness=0)
        self.fill = self.bar.create_rectangle(0, 0, 0, 4, width=0,
                                              fill=C.accent())

        self.canvas.bind("<Configure>", self._center)
        self.step = 0
        self.after(450, self._tick)

    def _center(self, event):
        w, h = event.width, event.height
        cx = w / 2
        self.canvas.coords("mini", cx - 56, h * 0.40)
        self.canvas.coords("pro", cx + 66, h * 0.40)
        # subtitle is the 3rd brand item; move by tag index via find
        items = self.canvas.find_withtag("brand")
        self.canvas.coords(items[-1], cx, h * 0.40 + 44)
        self.canvas.create_window(cx, h * 0.62, window=self.bar, tags="ui")
        self.canvas.delete("statuswin")
        self.canvas.create_window(cx, h * 0.62 + 26, window=self.status,
                                  tags="statuswin")

    def _tick(self):
        if self.step < len(BOOT_MESSAGES):
            msg = BOOT_MESSAGES[self.step]
            self.status.config(text=msg)
            log(msg, level="BOOT")
            progress = (self.step + 1) / len(BOOT_MESSAGES)
            self.bar.coords(self.fill, 0, 0, self.bar_w * progress, 4)
            self.step += 1
            self.after(420, self._tick)
        else:
            self.after(420, self.on_complete)
