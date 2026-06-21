"""ui/statusbar.py - Right-hand system info panel.

Live CPU/Memory rings, a system-statistics readout (processes, threads, memory,
disk, uptime, kernel state) and a running-apps list with green/grey indicators.
Everything is read from the kernel each second by the desktop's poll loop; this
panel only renders -- it holds no OS logic.
"""

import tkinter as tk

from ui import colors as C
from ui import fonts as F
from ui.widgets import GlassPanel, stat_row
from ui.rings import Ring


class InfoPanel(tk.Frame):
    def __init__(self, parent, width=290):
        super().__init__(parent, bg=C.bg(), width=width)
        self.pack_propagate(False)
        pad = dict(padx=14, pady=(14, 0))

        # Rings
        rings_panel = GlassPanel(self, title="Live Usage", icon="⚡")
        rings_panel.pack(fill="x", **pad)
        row = tk.Frame(rings_panel.body, bg=C.card())
        row.pack()
        self.cpu_ring = Ring(row, label="CPU", size=112, color=C.accent())
        self.cpu_ring.pack(side="left", padx=6)
        self.mem_ring = Ring(row, label="MEM", size=112, color=C.blue())
        self.mem_ring.pack(side="left", padx=6)

        # System statistics
        stats = GlassPanel(self, title="System", icon="🖥")
        stats.pack(fill="x", **pad)
        self.kernel_val = stat_row(stats.body, "Kernel", "Running", C.green())
        self.proc_val = stat_row(stats.body, "Processes", "0")
        self.thread_val = stat_row(stats.body, "Threads", "0")
        self.mem_val = stat_row(stats.body, "Memory", "0 MB")
        self.disk_val = stat_row(stats.body, "Disk", "0.0 GB")
        self.uptime_val = stat_row(stats.body, "Uptime", "00:00:00")

        # Running apps
        running = GlassPanel(self, title="Running", icon="🟢")
        running.pack(fill="both", expand=True, **pad)
        running.pack_configure(pady=14)
        self.running_body = running.body

    # ------------------------------------------------------------------ #
    def update_stats(self, *, cpu, mem_pct, processes, threads, mem_mb,
                     disk_gb, uptime):
        self.cpu_ring.set(cpu)
        self.mem_ring.set(mem_pct)
        self.proc_val.config(text=str(processes))
        self.thread_val.config(text=str(threads))
        self.mem_val.config(text=f"{mem_mb:.0f} MB")
        self.disk_val.config(text=f"{disk_gb:.1f} GB")
        self.uptime_val.config(text=uptime)

    def update_running(self, names):
        for child in self.running_body.winfo_children():
            child.destroy()
        if not names:
            tk.Label(self.running_body, text="No user apps open",
                     font=F.small(), fg=C.muted(),
                     bg=C.card()).pack(anchor="w")
            return
        for name in names:
            row = tk.Frame(self.running_body, bg=C.card())
            row.pack(fill="x", pady=2)
            tk.Label(row, text="●", font=F.small(), fg=C.green(),
                     bg=C.card()).pack(side="left", padx=(0, 8))
            tk.Label(row, text=name, font=F.body(), fg=C.text(),
                     bg=C.card()).pack(side="left")
