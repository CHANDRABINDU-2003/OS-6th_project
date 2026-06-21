"""apps/system_monitor.py - System Monitor Dashboard.

Real-time (simulated) gauges for CPU, memory and disk activity, plus a live
list of active processes pulled from the kernel registry.
"""

import tkinter as tk
from tkinter import ttk

from utils import Theme, make_label, center_window
from core.logger import log
from core.kernel import get_kernel


class SystemMonitorApp(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.title("System Monitor")
        self.configure(bg=Theme.BG)
        center_window(self, 600, 520)
        log("System Monitor opened")

        self.kernel = get_kernel()
        self._running = True
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        make_label(self, "System Monitor Dashboard", 16, bold=True,
                   bg=Theme.BG).pack(pady=(14, 10))

        gauges = tk.Frame(self, bg=Theme.BG)
        gauges.pack(fill="x", padx=16)
        self.cpu = self._make_gauge(gauges, "CPU")
        self.mem = self._make_gauge(gauges, "Memory")
        self.disk = self._make_gauge(gauges, "Disk")

        make_label(self, "Active Processes", 11, bold=True,
                   bg=Theme.BG).pack(anchor="w", padx=18, pady=(14, 4))
        self.tree = ttk.Treeview(self, columns=("pid", "name", "state"),
                                 show="headings", height=10)
        for c, t, w, a in (("pid", "PID", 80, "center"),
                           ("name", "Name", 300, "w"),
                           ("state", "State", 140, "center")):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor=a)
        self.tree.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        self._refresh()

    def _make_gauge(self, parent, title):
        f = tk.Frame(parent, bg=Theme.PANEL)
        f.pack(side="left", expand=True, fill="x", padx=6)
        make_label(f, title, 10, bold=True).pack(anchor="w", padx=10, pady=(8, 0))
        val = make_label(f, "0%", 20, bold=True, fg=Theme.ACCENT)
        val.pack(anchor="w", padx=10)
        canvas = tk.Canvas(f, height=12, bg=Theme.PANEL_LIGHT,
                           highlightthickness=0)
        canvas.pack(fill="x", padx=10, pady=(0, 10))
        bar = canvas.create_rectangle(0, 0, 0, 12, fill=Theme.ACCENT, width=0)
        return {"val": val, "canvas": canvas, "bar": bar}

    def _set_gauge(self, gauge, pct):
        gauge["val"].config(text=f"{pct:.0f}%")
        w = gauge["canvas"].winfo_width()
        gauge["canvas"].coords(gauge["bar"], 0, 0, w * pct / 100, 12)
        color = (Theme.ACCENT_3 if pct > 80
                 else Theme.ACCENT_4 if pct > 50 else Theme.ACCENT_2)
        gauge["canvas"].itemconfig(gauge["bar"], fill=color)
        gauge["val"].config(fg=color)

    def _refresh(self):
        if not self._running:
            return
        self._set_gauge(self.cpu, self.kernel.cpu_usage())
        self._set_gauge(self.mem, self.kernel.mem_usage())
        self._set_gauge(self.disk, self.kernel.disk_usage())

        self.tree.delete(*self.tree.get_children())
        procs = self.kernel.processes
        for p in procs:
            self.tree.insert("", "end",
                             values=(p["pid"], p["name"], p["state"]))
        if not procs:
            self.tree.insert("", "end", values=("-", "(no processes)", "-"))

        self.after(1200, self._refresh)

    def _on_close(self):
        self._running = False
        self.destroy()
