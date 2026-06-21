"""apps/process_state.py - Process State Simulator.

Visualises the classic five-state process lifecycle (NEW, READY, RUNNING,
WAITING, TERMINATED) on a Canvas. Each process is a coloured token that moves
between state boxes as the simulation ticks. Transitions follow a single-CPU
model: admit (NEW->READY), dispatch (READY->RUNNING), and the running process
then either exits, is preempted (->READY) or blocks on I/O (->WAITING); blocked
processes eventually complete I/O (->READY).

Self-contained: the tiny state machine lives here, no separate algorithm file.
Follows the reference app pattern in apps/scheduler.py.
"""

import random
import tkinter as tk
from tkinter import ttk

from utils import (Theme, make_label, make_button, center_window, color_for)
from core.logger import log

# The five lifecycle states, in left-to-right pipeline order, with the Theme
# accent each box is painted in.
STATES = ["NEW", "READY", "RUNNING", "WAITING", "TERMINATED"]
STATE_COLORS = {
    "NEW": "PANEL_LIGHT",
    "READY": "ACCENT",
    "RUNNING": "ACCENT_2",
    "WAITING": "ACCENT_4",
    "TERMINATED": "ACCENT_3",
}

# Legal transitions, drawn as labelled arrows between boxes.
TRANSITIONS = [
    ("NEW", "READY", "admit"),
    ("READY", "RUNNING", "dispatch"),
    ("RUNNING", "READY", "timeout"),
    ("RUNNING", "WAITING", "I/O wait"),
    ("RUNNING", "TERMINATED", "exit"),
    ("WAITING", "READY", "I/O done"),
]

CANVAS_W = 940
CANVAS_H = 420
BOX_W = 150
BOX_H = 240
BOX_TOP = 70


class ProcessStateApp(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.title("Process State Simulator")
        self.configure(bg=Theme.BG)
        center_window(self, 980, 720)
        log("Process State Simulator opened")

        self.processes = []      # list of {"pid", "state", "color"}
        self._next_pid = 1
        self._auto_id = None      # after() id when auto-stepping
        self._box_rects = {}      # state -> (x0, y0, x1, y1)

        make_label(self, "Process State Simulator", 16, bold=True,
                   bg=Theme.BG).pack(pady=(14, 2))
        make_label(self,
                   "Add processes, then Step (or Auto) to watch them move "
                   "through the lifecycle.",
                   10, fg=Theme.TEXT_DIM, bg=Theme.BG).pack()

        self._build_controls()
        self._build_canvas()
        self._build_table()

        self._draw_diagram()
        self._refresh()

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ------------------------------------------------------------------ #
    # UI construction
    # ------------------------------------------------------------------ #
    def _build_controls(self):
        bar = tk.Frame(self, bg=Theme.BG)
        bar.pack(fill="x", padx=16, pady=10)

        make_button(bar, "+ Add Process", self.add_process,
                    bg=Theme.PANEL_LIGHT).pack(side="left")
        make_button(bar, "Step", self.step,
                    bg=Theme.ACCENT_2).pack(side="left", padx=8)

        self.auto_btn = make_button(bar, "Auto: OFF", self.toggle_auto,
                                    bg=Theme.ACCENT)
        self.auto_btn.pack(side="left")

        self.status_lbl = make_label(bar, "", 10, fg=Theme.TEXT_DIM,
                                     bg=Theme.BG)
        self.status_lbl.pack(side="right")

    def _build_canvas(self):
        self.canvas = tk.Canvas(self, width=CANVAS_W, height=CANVAS_H,
                                bg=Theme.PANEL, highlightthickness=0)
        self.canvas.pack(padx=16, pady=(4, 8))

    def _build_table(self):
        make_label(self, "Process Table", 11, bold=True,
                   bg=Theme.BG).pack(pady=(4, 2))
        self.tree = ttk.Treeview(self, columns=("pid", "state"),
                                 show="headings", height=7)
        self.tree.heading("pid", text="PID")
        self.tree.heading("state", text="State")
        self.tree.column("pid", width=120, anchor="center")
        self.tree.column("state", width=180, anchor="center")
        self.tree.pack(fill="x", padx=16, pady=(0, 14))

    # ------------------------------------------------------------------ #
    # Static diagram: state boxes + transition arrows
    # ------------------------------------------------------------------ #
    def _draw_diagram(self):
        c = self.canvas
        gap = (CANVAS_W - len(STATES) * BOX_W) / (len(STATES) + 1)
        for i, state in enumerate(STATES):
            x0 = gap + i * (BOX_W + gap)
            x1 = x0 + BOX_W
            y0, y1 = BOX_TOP, BOX_TOP + BOX_H
            self._box_rects[state] = (x0, y0, x1, y1)
            color = getattr(Theme, STATE_COLORS[state])
            c.create_rectangle(x0, y0, x1, y1, fill=Theme.PANEL,
                               outline=color, width=3)
            c.create_rectangle(x0, y0, x1, y0 + 30, fill=color, outline=color)
            c.create_text((x0 + x1) / 2, y0 + 15, text=state,
                          fill=Theme.BG, font=(Theme.FONT, 11, "bold"))

        self._draw_transitions()

    def _draw_transitions(self):
        c = self.canvas
        # Stagger arrows vertically so labels do not overlap.
        offsets = {
            ("NEW", "READY"): 0,
            ("READY", "RUNNING"): 0,
            ("RUNNING", "TERMINATED"): 0,
            ("RUNNING", "WAITING"): 0,
            ("RUNNING", "READY"): -90,
            ("WAITING", "READY"): 90,
        }
        for src, dst, label in TRANSITIONS:
            sx0, sy0, sx1, sy1 = self._box_rects[src]
            dx0, dy0, dx1, dy1 = self._box_rects[dst]
            cy = (sy0 + sy1) / 2 + offsets.get((src, dst), 0)
            if dx0 > sx1:                       # arrow points right
                x_from, x_to = sx1, dx0
            else:                               # arrow points left
                x_from, x_to = sx0, dx1
            c.create_line(x_from, cy, x_to, cy, fill=Theme.TEXT_DIM,
                          width=2, arrow=tk.LAST, smooth=True)
            c.create_text((x_from + x_to) / 2, cy - 10, text=label,
                          fill=Theme.TEXT, font=(Theme.FONT, 8, "italic"))

    # ------------------------------------------------------------------ #
    # Process tokens
    # ------------------------------------------------------------------ #
    def _draw_tokens(self):
        self.canvas.delete("token")
        # Group processes by state so they can be stacked inside the box.
        by_state = {s: [] for s in STATES}
        for p in self.processes:
            by_state[p["state"]].append(p)

        for state, procs in by_state.items():
            x0, y0, x1, y1 = self._box_rects[state]
            cx = (x0 + x1) / 2
            top = y0 + 50
            r = 16
            step = 42
            for idx, p in enumerate(procs):
                cy = top + idx * step
                if cy + r > y1 - 8:            # keep tokens inside the box
                    cy = y1 - r - 8
                self.canvas.create_oval(cx - r, cy - r, cx + r, cy + r,
                                        fill=p["color"], outline=Theme.BG,
                                        width=2, tags="token")
                self.canvas.create_text(cx, cy, text=p["pid"], fill=Theme.BG,
                                        font=(Theme.FONT, 9, "bold"),
                                        tags="token")

    # ------------------------------------------------------------------ #
    # Simulation
    # ------------------------------------------------------------------ #
    def add_process(self):
        pid = f"P{self._next_pid}"
        self._next_pid += 1
        self.processes.append({
            "pid": pid,
            "state": "NEW",
            "color": color_for(len(self.processes)),
        })
        log(f"{pid}: created in NEW")
        self._refresh()

    def _by_state(self, state):
        return [p for p in self.processes if p["state"] == state]

    def _move(self, proc, new_state):
        old = proc["state"]
        proc["state"] = new_state
        log(f"{proc['pid']}: {old} -> {new_state}")

    def step(self):
        """Advance the simulation one tick with realistic transitions."""
        # 1. Admit one process: NEW -> READY.
        new_procs = self._by_state("NEW")
        if new_procs:
            self._move(new_procs[0], "READY")

        # 2. A waiting process may complete I/O: WAITING -> READY.
        waiting = self._by_state("WAITING")
        if waiting and random.random() < 0.6:
            self._move(random.choice(waiting), "READY")

        # 3. Single CPU: if one is RUNNING, let it run out its tick.
        running = self._by_state("RUNNING")
        if running:
            proc = running[0]
            outcome = random.choice(["TERMINATED", "READY", "WAITING"])
            self._move(proc, outcome)

        # 4. Dispatch a READY process to the (now free) CPU.
        if not self._by_state("RUNNING"):
            ready = self._by_state("READY")
            if ready:
                self._move(ready[0], "RUNNING")

        self._refresh()

    def toggle_auto(self):
        if self._auto_id is None:
            self.auto_btn.config(text="Auto: ON")
            self._auto_tick()
        else:
            self.after_cancel(self._auto_id)
            self._auto_id = None
            self.auto_btn.config(text="Auto: OFF")

    def _auto_tick(self):
        self.step()
        self._auto_id = self.after(1000, self._auto_tick)

    # ------------------------------------------------------------------ #
    # Refresh views
    # ------------------------------------------------------------------ #
    def _refresh(self):
        self._draw_tokens()
        self.tree.delete(*self.tree.get_children())
        for p in self.processes:
            self.tree.insert("", "end", values=(p["pid"], p["state"]))

        active = len([p for p in self.processes
                      if p["state"] != "TERMINATED"])
        done = len(self._by_state("TERMINATED"))
        self.status_lbl.config(
            text=f"Total: {len(self.processes)}   Active: {active}   "
                 f"Terminated: {done}")

    def _on_close(self):
        if self._auto_id is not None:
            self.after_cancel(self._auto_id)
            self._auto_id = None
        log("Process State Simulator closed")
        self.destroy()
