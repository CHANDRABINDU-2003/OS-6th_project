"""apps/scheduler.py - CPU Scheduling GUI.

Thin Tkinter front-end over algorithms/cpu_scheduling.py. Supports FCFS, SJF,
Priority, Round Robin and Multilevel Queue, with a Gantt chart and averages.

This module is the reference pattern for every app:
  * subclass tk.Toplevel
  * log launch via core.logger.log
  * build UI with utils widget factories + Theme
"""

import tkinter as tk
from tkinter import ttk, messagebox

from utils import (Theme, make_label, make_button, make_entry,
                   center_window, color_for, read_json, PROCESSES_FILE)
from core.logger import log
from algorithms import cpu_scheduling as cpu


class SchedulerApp(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.title("CPU Scheduler")
        self.configure(bg=Theme.BG)
        center_window(self, 880, 660)
        log("CPU Scheduler opened")

        self.rows = []  # (pid_e, arrival_e, burst_e, priority_e)

        make_label(self, "CPU Scheduling Simulator", 16, bold=True,
                   bg=Theme.BG).pack(pady=(14, 2))
        make_label(self, "Add processes, pick an algorithm, then Run.",
                   10, fg=Theme.TEXT_DIM, bg=Theme.BG).pack()

        self._build_input_area()
        self._build_controls()
        self._build_output_area()
        self._load_sample()

    # ------------------------------------------------------------------ #
    def _build_input_area(self):
        wrap = tk.Frame(self, bg=Theme.PANEL)
        wrap.pack(fill="x", padx=16, pady=10)

        header = tk.Frame(wrap, bg=Theme.PANEL)
        header.pack(fill="x", padx=8, pady=(8, 2))
        for i, t in enumerate(("PID", "Arrival", "Burst", "Priority", "")):
            make_label(header, t, 10, bold=True).grid(
                row=0, column=i, padx=10, sticky="w")

        self.rows_holder = tk.Frame(wrap, bg=Theme.PANEL)
        self.rows_holder.pack(fill="x", padx=8, pady=(0, 8))

    def _add_row(self, pid="", arrival="", burst="", priority=""):
        rf = tk.Frame(self.rows_holder, bg=Theme.PANEL)
        rf.pack(fill="x", pady=2)
        entries = []
        for col, val in enumerate((pid, arrival, burst, priority)):
            e = make_entry(rf, width=10)
            e.insert(0, str(val))
            e.grid(row=0, column=col, padx=10)
            entries.append(e)

        def remove():
            rf.destroy()
            if tuple(entries) in self.rows:
                self.rows.remove(tuple(entries))

        make_button(rf, "✕", remove, bg=Theme.ACCENT_3).grid(
            row=0, column=4, padx=10)
        self.rows.append(tuple(entries))

    def _build_controls(self):
        bar = tk.Frame(self, bg=Theme.BG)
        bar.pack(fill="x", padx=16)

        make_button(bar, "+ Add Process",
                    lambda: self._add_row(f"P{len(self.rows) + 1}", 0, 1, 1),
                    bg=Theme.PANEL_LIGHT).pack(side="left")

        make_label(bar, "Algorithm:", 10, bg=Theme.BG).pack(
            side="left", padx=(20, 6))
        self.algo = tk.StringVar(value="FCFS")
        ttk.Combobox(bar, textvariable=self.algo, state="readonly", width=16,
                     values=["FCFS", "SJF", "Priority", "Round Robin",
                             "Multilevel Queue"]).pack(side="left")

        make_label(bar, "Quantum:", 10, bg=Theme.BG).pack(side="left", padx=(16, 4))
        self.quantum = make_entry(bar, width=5)
        self.quantum.insert(0, "2")
        self.quantum.pack(side="left")

        make_button(bar, "▶ Run", self.run, bg=Theme.ACCENT_2).pack(side="right")

    def _build_output_area(self):
        self.tree = ttk.Treeview(
            self, columns=("pid", "arr", "burst", "comp", "tat", "wt"),
            show="headings", height=6)
        for c, t in zip(
                ("pid", "arr", "burst", "comp", "tat", "wt"),
                ("PID", "Arrival", "Burst", "Completion", "Turnaround", "Waiting")):
            self.tree.heading(c, text=t)
            self.tree.column(c, width=110, anchor="center")
        self.tree.pack(fill="x", padx=16, pady=(12, 6))

        self.avg_lbl = make_label(self, "", 11, bold=True, bg=Theme.BG)
        self.avg_lbl.pack()

        make_label(self, "Gantt Chart", 11, bold=True, bg=Theme.BG).pack(pady=(8, 2))
        self.gantt = tk.Canvas(self, height=90, bg=Theme.PANEL,
                               highlightthickness=0)
        self.gantt.pack(fill="x", padx=16, pady=(0, 14))

    # ------------------------------------------------------------------ #
    def _load_sample(self):
        for p in read_json(PROCESSES_FILE, []):
            self._add_row(p["pid"], p["arrival"], p["burst"], p["priority"])

    def _collect(self):
        procs = []
        for pid_e, arr_e, burst_e, pri_e in self.rows:
            pid = pid_e.get().strip()
            if not pid:
                continue
            try:
                procs.append({
                    "pid": pid,
                    "arrival": int(arr_e.get()),
                    "burst": int(burst_e.get()),
                    "priority": int(pri_e.get() or 0),
                })
            except ValueError:
                raise ValueError(f"Invalid numbers for process '{pid}'.")
        if not procs:
            raise ValueError("Add at least one process.")
        return procs

    def run(self):
        try:
            procs = self._collect()
            algo = self.algo.get()
            if algo == "FCFS":
                results, timeline = cpu.fcfs(procs)
            elif algo == "SJF":
                results, timeline = cpu.sjf(procs)
            elif algo == "Priority":
                results, timeline = cpu.priority_np(procs)
            elif algo == "Round Robin":
                results, timeline = cpu.round_robin(procs, int(self.quantum.get()))
            else:
                results, timeline = cpu.multilevel_queue(
                    procs, int(self.quantum.get()))
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        log(f"Scheduler ran {algo} on {len(procs)} processes")
        self._show_results(results, timeline)

    def _show_results(self, results, timeline):
        self.tree.delete(*self.tree.get_children())
        for r in results:
            self.tree.insert("", "end", values=(
                r["pid"], r["arrival"], r["burst"],
                r["completion"], r["turnaround"], r["waiting"]))

        avg_tat, avg_wt = cpu.averages(results)
        self.avg_lbl.config(
            text=f"Average Turnaround: {avg_tat:.2f}    "
                 f"Average Waiting: {avg_wt:.2f}")
        self._draw_gantt(timeline)

    def _draw_gantt(self, timeline):
        c = self.gantt
        c.delete("all")
        if not timeline:
            return
        c.update_idletasks()
        total = timeline[-1][2] - timeline[0][1]
        if total <= 0:
            return
        margin = 20
        width = c.winfo_width() - 2 * margin
        scale = width / total
        origin = timeline[0][1]
        pid_color = {}
        for pid, start, end in timeline:
            if pid not in pid_color:
                pid_color[pid] = color_for(len(pid_color))
            x0 = margin + (start - origin) * scale
            x1 = margin + (end - origin) * scale
            c.create_rectangle(x0, 20, x1, 55, fill=pid_color[pid],
                               outline=Theme.BG, width=2)
            c.create_text((x0 + x1) / 2, 37, text=pid,
                          fill="#1e2030", font=(Theme.FONT, 10, "bold"))
            c.create_text(x0, 65, text=str(start), fill=Theme.TEXT_DIM,
                          font=(Theme.FONT, 8))
        last_x = margin + (timeline[-1][2] - origin) * scale
        c.create_text(last_x, 65, text=str(timeline[-1][2]),
                      fill=Theme.TEXT_DIM, font=(Theme.FONT, 8))
