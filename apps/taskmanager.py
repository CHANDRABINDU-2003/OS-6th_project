"""apps/taskmanager.py - Task Manager.

Shows the kernel's live process table: every system process, open app window
and simulated workload process, with its state, CPU% and memory. Everything is
read straight from the kernel (core.kernel.get_kernel()), so the numbers are
real -- they reflect actual process states, not random fluctuations. Selecting
a process and pressing "End Task" terminates it through the kernel.
"""

import tkinter as tk
from tkinter import ttk

from utils import Theme, make_label, make_button, center_window
from core.logger import log
from core.kernel import get_kernel
from core.pcb import ProcessState


# State -> row tag colour, so the table reads at a glance.
_STATE_COLORS = {
    ProcessState.RUNNING: Theme.ACCENT_2,
    ProcessState.READY: Theme.ACCENT,
    ProcessState.WAITING: Theme.ACCENT_4,
    ProcessState.NEW: Theme.TEXT_DIM,
}


class TaskManagerApp(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.title("Task Manager")
        self.configure(bg=Theme.BG)
        center_window(self, 660, 480)

        self.kernel = get_kernel()
        self._running = True
        self.protocol("WM_DELETE_WINDOW", self._on_close)

        self._build_ui()
        self._refresh()
        log("Task Manager opened")

    def _build_ui(self):
        make_label(self, "Task Manager", 16, bold=True,
                   bg=Theme.BG).pack(pady=(14, 8))

        # Gauges
        gauges = tk.Frame(self, bg=Theme.BG)
        gauges.pack(fill="x", padx=16)
        self.cpu_gauge = self._make_gauge(gauges, "CPU")
        self.mem_gauge = self._make_gauge(gauges, "Memory")

        # Process table
        self.tree = ttk.Treeview(
            self, columns=("pid", "name", "state", "cpu", "mem"),
            show="headings", height=11)
        for c, t, w in (("pid", "PID", 60), ("name", "Name", 200),
                        ("state", "State", 100), ("cpu", "CPU %", 100),
                        ("mem", "Memory (MB)", 120)):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w, anchor="center")
        for state, color in _STATE_COLORS.items():
            self.tree.tag_configure(state, foreground=color)
        self.tree.pack(fill="both", expand=True, padx=16, pady=12)

        make_button(self, "End Task", self.end_task,
                    bg=Theme.ACCENT_3).pack(pady=(0, 12))

    def _make_gauge(self, parent, title):
        f = tk.Frame(parent, bg=Theme.PANEL)
        f.pack(side="left", expand=True, fill="x", padx=6)
        make_label(f, title, 10, bold=True).pack(anchor="w", padx=8, pady=(6, 0))
        lbl = make_label(f, "0%", 18, bold=True, fg=Theme.ACCENT)
        lbl.pack(anchor="w", padx=8)
        canvas = tk.Canvas(f, height=10, bg=Theme.PANEL_LIGHT,
                           highlightthickness=0)
        canvas.pack(fill="x", padx=8, pady=(0, 8))
        bar = canvas.create_rectangle(0, 0, 0, 10, fill=Theme.ACCENT, width=0)
        return {"label": lbl, "canvas": canvas, "bar": bar}

    def _set_gauge(self, gauge, pct):
        gauge["label"].config(text=f"{pct:.0f}%")
        w = gauge["canvas"].winfo_width()
        gauge["canvas"].coords(gauge["bar"], 0, 0, w * pct / 100, 10)
        color = (Theme.ACCENT_3 if pct > 80
                 else Theme.ACCENT_4 if pct > 50 else Theme.ACCENT_2)
        gauge["canvas"].itemconfig(gauge["bar"], fill=color)
        gauge["label"].config(fg=color)

    def _refresh(self):
        if not self._running:
            return

        rows = sorted(self.kernel.live_processes(),
                      key=lambda p: (-p.cpu_share(), p.pid))
        self.tree.delete(*self.tree.get_children())
        for p in rows:
            self.tree.insert(
                "", "end", iid=str(p.pid), tags=(p.state,),
                values=(p.pid, p.name, p.state,
                        f"{p.cpu_share():.1f}", f"{p.display_mem():.1f}"))

        self._set_gauge(self.cpu_gauge, self.kernel.cpu_usage())
        self._set_gauge(self.mem_gauge, self.kernel.mem_usage())

        self.after(1000, self._refresh)

    def end_task(self):
        sel = self.tree.selection()
        if not sel:
            return
        pid = int(sel[0])
        self.kernel.terminate(pid)
        self._refresh()

    def _on_close(self):
        self._running = False
        self.destroy()
