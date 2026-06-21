"""apps/kernel_log.py - Kernel Log Window.

Shows a live feed of kernel events (boot, process launches, memory activity,
logins...). Subscribes to core.logger so new lines appear in real time.
"""

import tkinter as tk

from utils import Theme, make_label, make_button, center_window
from core import logger
from core.logger import log


class KernelLogApp(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.title("Kernel Log")
        self.configure(bg=Theme.BG)
        center_window(self, 640, 460)

        make_label(self, "Kernel Log", 16, bold=True, bg=Theme.BG).pack(
            pady=(12, 6))

        self.text = tk.Text(self, bg="#0b0b12", fg=Theme.ACCENT_2,
                            insertbackground=Theme.TEXT, relief="flat",
                            font=(Theme.FONT_MONO, 10), wrap="none")
        self.text.pack(fill="both", expand=True, padx=12, pady=(0, 6))
        self.text.config(state="disabled")

        bar = tk.Frame(self, bg=Theme.BG)
        bar.pack(fill="x", padx=12, pady=(0, 10))
        make_button(bar, "Clear View", self._clear,
                    bg=Theme.PANEL_LIGHT).pack(side="right")

        # Render the existing buffer, then subscribe for live updates.
        for line in logger.get_logs():
            self._append(line)
        logger.subscribe(self._append)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        log("Kernel Log opened")

    def _append(self, line):
        self.text.config(state="normal")
        self.text.insert("end", line + "\n")
        self.text.see("end")
        self.text.config(state="disabled")

    def _clear(self):
        self.text.config(state="normal")
        self.text.delete("1.0", "end")
        self.text.config(state="disabled")

    def _on_close(self):
        logger.unsubscribe(self._append)
        self.destroy()
