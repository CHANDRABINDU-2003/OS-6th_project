"""apps/disk_scheduler.py - Disk Scheduling GUI.

Thin Tkinter front-end over algorithms/disk_algo.py. Supports FCFS, SSTF,
SCAN, C-SCAN and LOOK, showing the total head movement (seek count) and a
line chart of the head's path across the cylinders.

Follows the reference app pattern (see apps/scheduler.py):
  * subclass tk.Toplevel
  * log launch via core.logger.log
  * build UI with utils widget factories + Theme
"""

import tkinter as tk
from tkinter import ttk, messagebox

from utils import (Theme, make_label, make_button, make_entry,
                   center_window)
from core.logger import log
from algorithms import disk_algo as disk


class DiskSchedulerApp(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.title("Disk Scheduler")
        self.configure(bg=Theme.BG)
        center_window(self, 880, 660)
        log("Disk Scheduler opened")

        make_label(self, "Disk Scheduling Simulator", 16, bold=True,
                   bg=Theme.BG).pack(pady=(14, 2))
        make_label(self, "Enter requests, pick an algorithm, then Run.",
                   10, fg=Theme.TEXT_DIM, bg=Theme.BG).pack()

        self._build_input_area()
        self._build_controls()
        self._build_output_area()

    # ------------------------------------------------------------------ #
    def _build_input_area(self):
        wrap = tk.Frame(self, bg=Theme.PANEL)
        wrap.pack(fill="x", padx=16, pady=10)

        grid = tk.Frame(wrap, bg=Theme.PANEL)
        grid.pack(fill="x", padx=8, pady=8)

        make_label(grid, "Requests:", 10, bold=True).grid(
            row=0, column=0, padx=10, pady=4, sticky="w")
        self.requests_e = make_entry(grid, width=40)
        self.requests_e.insert(0, "98 183 37 122 14 124 65 67")
        self.requests_e.grid(row=0, column=1, columnspan=3, padx=10,
                             pady=4, sticky="w")

        make_label(grid, "Head:", 10, bold=True).grid(
            row=1, column=0, padx=10, pady=4, sticky="w")
        self.head_e = make_entry(grid, width=10)
        self.head_e.insert(0, "53")
        self.head_e.grid(row=1, column=1, padx=10, pady=4, sticky="w")

        make_label(grid, "Disk size:", 10, bold=True).grid(
            row=1, column=2, padx=10, pady=4, sticky="w")
        self.disk_e = make_entry(grid, width=10)
        self.disk_e.insert(0, "200")
        self.disk_e.grid(row=1, column=3, padx=10, pady=4, sticky="w")

    def _build_controls(self):
        bar = tk.Frame(self, bg=Theme.BG)
        bar.pack(fill="x", padx=16)

        make_label(bar, "Algorithm:", 10, bg=Theme.BG).pack(
            side="left", padx=(0, 6))
        self.algo = tk.StringVar(value="FCFS")
        ttk.Combobox(bar, textvariable=self.algo, state="readonly", width=12,
                     values=["FCFS", "SSTF", "SCAN", "C-SCAN", "LOOK"]).pack(
            side="left")

        make_label(bar, "Direction:", 10, bg=Theme.BG).pack(
            side="left", padx=(16, 6))
        self.direction = tk.StringVar(value="up")
        ttk.Combobox(bar, textvariable=self.direction, state="readonly",
                     width=8, values=["up", "down"]).pack(side="left")

        make_button(bar, "▶ Run", self.run, bg=Theme.ACCENT_2).pack(side="right")

    def _build_output_area(self):
        self.seek_lbl = make_label(self, "", 14, bold=True, bg=Theme.BG,
                                   fg=Theme.ACCENT_2)
        self.seek_lbl.pack(pady=(12, 2))

        self.seq_lbl = make_label(self, "", 10, fg=Theme.TEXT_DIM, bg=Theme.BG)
        self.seq_lbl.pack(pady=(0, 6))

        make_label(self, "Head Movement", 11, bold=True, bg=Theme.BG).pack(
            pady=(4, 2))
        self.canvas = tk.Canvas(self, height=380, bg=Theme.PANEL,
                                highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=16, pady=(0, 14))

    # ------------------------------------------------------------------ #
    def _collect(self):
        """Parse and validate the inputs, returning (requests, head, size)."""
        try:
            requests = [int(tok) for tok in self.requests_e.get().split()]
        except ValueError:
            raise ValueError("Requests must be space-separated integers.")
        if not requests:
            raise ValueError("Enter at least one request.")

        try:
            head = int(self.head_e.get())
            size = int(self.disk_e.get())
        except ValueError:
            raise ValueError("Head and disk size must be integers.")
        if size <= 0:
            raise ValueError("Disk size must be positive.")
        if not (0 <= head < size):
            raise ValueError("Head must be within 0..disk_size-1.")
        if any(not (0 <= r < size) for r in requests):
            raise ValueError("All requests must be within 0..disk_size-1.")
        return requests, head, size

    def run(self):
        try:
            requests, head, size = self._collect()
            algo = self.algo.get()
            direction = self.direction.get()
            if algo == "FCFS":
                sequence, total = disk.fcfs(requests, head)
            elif algo == "SSTF":
                sequence, total = disk.sstf(requests, head)
            elif algo == "SCAN":
                sequence, total = disk.scan(requests, head, size, direction)
            elif algo == "C-SCAN":
                sequence, total = disk.cscan(requests, head, size, direction)
            else:  # LOOK
                sequence, total = disk.look(requests, head, direction)
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        log(f"Disk Scheduler ran {algo}, total seek = {total}")
        self.seek_lbl.config(text=f"Total Seek Operations: {total}")
        self.seq_lbl.config(text="  ->  ".join(str(p) for p in sequence))
        self._draw_path(sequence, size)

    def _draw_path(self, sequence, size):
        """Visualise the head path as a line chart.

        x-axis = cylinder position (0..disk_size), y-axis = step order going
        downward. Visited positions are connected with a line and marked with
        dots labelled by their cylinder number.
        """
        c = self.canvas
        c.delete("all")
        c.update_idletasks()

        w = c.winfo_width()
        h = c.winfo_height()
        if w <= 1 or h <= 1:
            # Canvas not yet laid out; retry once it has a real size.
            c.after(50, lambda: self._draw_path(sequence, size))
            return

        margin_x = 50
        margin_top = 30
        margin_bottom = 20
        plot_w = w - 2 * margin_x
        plot_h = h - margin_top - margin_bottom

        def x_of(pos):
            return margin_x + (pos / max(size - 1, 1)) * plot_w

        steps = max(len(sequence) - 1, 1)

        def y_of(step):
            return margin_top + (step / steps) * plot_h

        # Axis scale labels along the top (cylinder positions).
        for frac in (0, 0.25, 0.5, 0.75, 1.0):
            pos = round(frac * (size - 1))
            x = x_of(pos)
            c.create_line(x, margin_top, x, h - margin_bottom,
                          fill=Theme.PANEL_LIGHT)
            c.create_text(x, margin_top - 14, text=str(pos),
                          fill=Theme.TEXT_DIM, font=(Theme.FONT, 8))

        # Connecting path.
        points = [(x_of(pos), y_of(i)) for i, pos in enumerate(sequence)]
        for i in range(1, len(points)):
            x0, y0 = points[i - 1]
            x1, y1 = points[i]
            c.create_line(x0, y0, x1, y1, fill=Theme.ACCENT, width=2)

        # Dots + position labels.
        for i, (x, y) in enumerate(points):
            color = Theme.ACCENT_3 if i == 0 else Theme.ACCENT_2
            c.create_oval(x - 4, y - 4, x + 4, y + 4, fill=color,
                          outline=Theme.BG)
            c.create_text(x, y - 12, text=str(sequence[i]),
                          fill=Theme.TEXT, font=(Theme.FONT, 8, "bold"))
