"""apps/page_replacement.py - Page Replacement GUI.

Thin Tkinter front-end over algorithms/page_replacement_algo.py. Supports FIFO,
LRU and Optimal replacement, showing total faults / hits / hit ratio plus a
per-step frame visualisation (faults in red, hits in green).

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
from algorithms import page_replacement_algo as pra


EXAMPLE_STRING = "7 0 1 2 0 3 0 4 2 3 0 3 2"
EXAMPLE_FRAMES = "3"


class PageReplacementApp(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.title("Page Replacement")
        self.configure(bg=Theme.BG)
        center_window(self, 920, 660)
        log("Page Replacement opened")

        make_label(self, "Page Replacement Simulator", 16, bold=True,
                   bg=Theme.BG).pack(pady=(14, 2))
        make_label(self,
                   "Enter a reference string and frame count, pick an "
                   "algorithm, then Run.",
                   10, fg=Theme.TEXT_DIM, bg=Theme.BG).pack()

        self._build_controls()
        self._build_summary()
        self._build_visualization()
        self._prefill()

    # ------------------------------------------------------------------ #
    def _build_controls(self):
        wrap = tk.Frame(self, bg=Theme.PANEL)
        wrap.pack(fill="x", padx=16, pady=10)

        bar = tk.Frame(wrap, bg=Theme.PANEL)
        bar.pack(fill="x", padx=8, pady=8)

        make_label(bar, "Reference String:", 10, bold=True).grid(
            row=0, column=0, padx=(0, 6), pady=4, sticky="w")
        self.ref_entry = make_entry(bar, width=40)
        self.ref_entry.grid(row=0, column=1, columnspan=3, padx=6, pady=4,
                            sticky="w")

        make_label(bar, "Frames:", 10, bold=True).grid(
            row=1, column=0, padx=(0, 6), pady=4, sticky="w")
        self.frames_entry = make_entry(bar, width=6)
        self.frames_entry.grid(row=1, column=1, padx=6, pady=4, sticky="w")

        make_label(bar, "Algorithm:", 10, bold=True).grid(
            row=1, column=2, padx=(16, 6), pady=4, sticky="e")
        self.algo = tk.StringVar(value="FIFO")
        ttk.Combobox(bar, textvariable=self.algo, state="readonly", width=12,
                     values=["FIFO", "LRU", "Optimal"]).grid(
            row=1, column=3, padx=6, pady=4, sticky="w")

        make_button(bar, "▶ Run", self.run, bg=Theme.ACCENT_2).grid(
            row=0, column=4, rowspan=2, padx=(20, 0), pady=4, sticky="e")

    def _build_summary(self):
        self.summary_lbl = make_label(self, "", 13, bold=True, bg=Theme.BG)
        self.summary_lbl.pack(pady=(4, 6))

    def _build_visualization(self):
        make_label(self, "Step-by-Step Frame Table", 11, bold=True,
                   bg=Theme.BG).pack(pady=(6, 2))

        outer = tk.Frame(self, bg=Theme.PANEL)
        outer.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        self.canvas = tk.Canvas(outer, bg=Theme.PANEL, highlightthickness=0)
        hbar = ttk.Scrollbar(outer, orient="horizontal",
                             command=self.canvas.xview)
        self.canvas.configure(xscrollcommand=hbar.set)
        hbar.pack(side="bottom", fill="x")
        self.canvas.pack(side="top", fill="both", expand=True)

        legend = tk.Frame(self, bg=Theme.BG)
        legend.pack(pady=(0, 8))
        tk.Label(legend, text="  ", bg=Theme.ACCENT_3).pack(side="left")
        make_label(legend, " Fault   ", 9, bg=Theme.BG).pack(side="left")
        tk.Label(legend, text="  ", bg=Theme.ACCENT_2).pack(side="left")
        make_label(legend, " Hit", 9, bg=Theme.BG).pack(side="left")

    # ------------------------------------------------------------------ #
    def _prefill(self):
        self.ref_entry.insert(0, EXAMPLE_STRING)
        self.frames_entry.insert(0, EXAMPLE_FRAMES)

    def _collect(self):
        """Parse the inputs into (pages, frames). Raises ValueError on error."""
        raw = self.ref_entry.get().replace(",", " ").split()
        if not raw:
            raise ValueError("Enter at least one page reference.")
        try:
            pages = [int(tok) for tok in raw]
        except ValueError:
            raise ValueError("Reference string must contain only integers.")
        try:
            frames = int(self.frames_entry.get())
        except ValueError:
            raise ValueError("Frames must be an integer.")
        if frames <= 0:
            raise ValueError("Frames must be a positive integer.")
        return pages, frames

    def run(self):
        try:
            pages, frames = self._collect()
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        algo = self.algo.get()
        if algo == "FIFO":
            result = pra.fifo(pages, frames)
        elif algo == "LRU":
            result = pra.lru(pages, frames)
        else:
            result = pra.optimal(pages, frames)

        log(f"Page Replacement ran {algo}: {result['faults']} faults")
        self._show_result(result, frames)

    def _show_result(self, result, frames):
        self.summary_lbl.config(
            text=f"Page Faults: {result['faults']}     "
                 f"Hits: {result['hits']}     "
                 f"Hit Ratio: {result['hit_ratio']:.2%}")
        self._draw_table(result["steps"], frames)

    def _draw_table(self, steps, frames):
        c = self.canvas
        c.delete("all")

        col_w = 48
        row_h = 36
        left = 90          # space for the row labels
        top = 30           # space for the page-reference header

        # --- Row labels (left column) ------------------------------------ #
        c.create_text(left // 2, top - 14, text="Page",
                      fill=Theme.TEXT, font=(Theme.FONT, 9, "bold"))
        for f in range(frames):
            y = top + f * row_h + row_h // 2
            c.create_text(left // 2, y, text=f"Frame {f}",
                          fill=Theme.TEXT_DIM, font=(Theme.FONT, 9))
        status_y = top + frames * row_h + row_h // 2

        # --- One column per step ----------------------------------------- #
        for i, step in enumerate(steps):
            x0 = left + i * col_w
            x1 = x0 + col_w
            cells = step["frames"]
            is_fault = step["fault"]
            mark_color = Theme.ACCENT_3 if is_fault else Theme.ACCENT_2

            # Header: the referenced page.
            c.create_text((x0 + x1) / 2, top - 14, text=str(step["page"]),
                          fill=Theme.TEXT, font=(Theme.FONT, 10, "bold"))

            # Frame slots, stacked vertically.
            for f in range(frames):
                y0 = top + f * row_h
                y1 = y0 + row_h
                value = str(cells[f]) if f < len(cells) else ""
                fill = mark_color if (f < len(cells)) else Theme.PANEL_LIGHT
                c.create_rectangle(x0 + 2, y0 + 2, x1 - 2, y1 - 2,
                                   fill=fill, outline=Theme.BG, width=1)
                if value:
                    c.create_text((x0 + x1) / 2, (y0 + y1) / 2, text=value,
                                  fill="#1e2030",
                                  font=(Theme.FONT, 11, "bold"))

            # Status row: F (fault) / H (hit).
            c.create_text((x0 + x1) / 2, status_y,
                          text="F" if is_fault else "H",
                          fill=mark_color, font=(Theme.FONT, 10, "bold"))

        total_w = left + len(steps) * col_w + 20
        total_h = status_y + row_h
        c.configure(scrollregion=(0, 0, max(total_w, 1), total_h))
