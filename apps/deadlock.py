"""apps/deadlock.py - Deadlock detection / avoidance GUI (Banker's Algorithm).

Thin Tkinter front-end over algorithms/bankers.py. Lets the user edit the
Allocation / Max matrices and the Available vector, checks for a safe state,
shows the computed Need matrix and draws a simple Resource Allocation Graph.

Follows the reference app pattern (see apps/scheduler.py).
"""

import tkinter as tk
from tkinter import ttk, messagebox

from utils import (Theme, make_label, make_button, make_entry, center_window)
from core.logger import log
from algorithms import bankers


# Classic textbook safe example: 5 processes, 3 resources.
DEFAULT_ALLOC = [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]]
DEFAULT_MAX = [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]]
DEFAULT_AVAIL = [3, 3, 2]


class DeadlockApp(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.title("Deadlock - Banker's Algorithm")
        self.configure(bg=Theme.BG)
        center_window(self, 920, 720)
        log("Deadlock opened")

        self.num_proc = len(DEFAULT_ALLOC)
        self.num_res = len(DEFAULT_ALLOC[0])
        self.alloc_entries = []   # list[list[Entry]]
        self.max_entries = []     # list[list[Entry]]
        self.avail_entries = []   # list[Entry]

        make_label(self, "Banker's Algorithm - Deadlock Avoidance", 16,
                   bold=True, bg=Theme.BG).pack(pady=(14, 2))
        make_label(self, "Edit the matrices, then check for a safe state.",
                   10, fg=Theme.TEXT_DIM, bg=Theme.BG).pack()

        self._build_dimensions()
        self._build_matrices()
        self._build_controls()
        self._build_output()

    # ------------------------------------------------------------------ #
    def _build_dimensions(self):
        bar = tk.Frame(self, bg=Theme.BG)
        bar.pack(fill="x", padx=16, pady=(10, 4))

        make_label(bar, "Processes:", 10, bg=Theme.BG).pack(side="left")
        self.proc_e = make_entry(bar, width=4)
        self.proc_e.insert(0, str(self.num_proc))
        self.proc_e.pack(side="left", padx=(4, 16))

        make_label(bar, "Resources:", 10, bg=Theme.BG).pack(side="left")
        self.res_e = make_entry(bar, width=4)
        self.res_e.insert(0, str(self.num_res))
        self.res_e.pack(side="left", padx=(4, 16))

        make_button(bar, "Rebuild Grids", self._rebuild,
                    bg=Theme.PANEL_LIGHT).pack(side="left")

    def _build_matrices(self):
        self.matrix_wrap = tk.Frame(self, bg=Theme.BG)
        self.matrix_wrap.pack(fill="x", padx=16, pady=6)
        self._populate_matrices(DEFAULT_ALLOC, DEFAULT_MAX, DEFAULT_AVAIL)

    def _populate_matrices(self, alloc, mx, avail):
        """(Re)build the editable grids, prefilling the given values."""
        for child in self.matrix_wrap.winfo_children():
            child.destroy()
        self.alloc_entries, self.max_entries, self.avail_entries = [], [], []

        alloc_panel = self._grid_panel("Allocation", self.alloc_entries, alloc)
        alloc_panel.pack(side="left", padx=(0, 10))
        max_panel = self._grid_panel("Max", self.max_entries, mx)
        max_panel.pack(side="left", padx=10)
        self._avail_panel(avail).pack(side="left", padx=10, anchor="n")

    def _grid_panel(self, title, store, values):
        """Build one labelled P x R grid of entries; append rows into store."""
        panel = tk.Frame(self.matrix_wrap, bg=Theme.PANEL)
        make_label(panel, title, 11, bold=True).grid(
            row=0, column=0, columnspan=self.num_res + 1, pady=(6, 4), padx=6)

        for j in range(self.num_res):
            make_label(panel, f"R{j}", 9, fg=Theme.TEXT_DIM).grid(
                row=1, column=j + 1, padx=3)

        for i in range(self.num_proc):
            make_label(panel, f"P{i}", 9, fg=Theme.TEXT_DIM).grid(
                row=i + 2, column=0, padx=4)
            row = []
            for j in range(self.num_res):
                e = make_entry(panel, width=4)
                val = values[i][j] if i < len(values) and j < len(values[i]) else 0
                e.insert(0, str(val))
                e.grid(row=i + 2, column=j + 1, padx=3, pady=2)
                row.append(e)
            store.append(row)
        return panel

    def _avail_panel(self, values):
        panel = tk.Frame(self.matrix_wrap, bg=Theme.PANEL)
        make_label(panel, "Available", 11, bold=True).grid(
            row=0, column=0, columnspan=self.num_res, pady=(6, 4), padx=6)
        for j in range(self.num_res):
            make_label(panel, f"R{j}", 9, fg=Theme.TEXT_DIM).grid(
                row=1, column=j, padx=3)
            e = make_entry(panel, width=4)
            val = values[j] if j < len(values) else 0
            e.insert(0, str(val))
            e.grid(row=2, column=j, padx=3, pady=2)
            self.avail_entries.append(e)
        return panel

    def _build_controls(self):
        bar = tk.Frame(self, bg=Theme.BG)
        bar.pack(fill="x", padx=16, pady=(4, 2))
        make_button(bar, "Check Safe State", self.check,
                    bg=Theme.ACCENT_2).pack(side="left")
        self.result_lbl = make_label(bar, "", 12, bold=True, bg=Theme.BG)
        self.result_lbl.pack(side="left", padx=16)

    def _build_output(self):
        lower = tk.Frame(self, bg=Theme.BG)
        lower.pack(fill="both", expand=True, padx=16, pady=(6, 14))

        left = tk.Frame(lower, bg=Theme.BG)
        left.pack(side="left", fill="y")
        make_label(left, "Need Matrix (Max - Allocation)", 11, bold=True,
                   bg=Theme.BG).pack(anchor="w", pady=(0, 4))
        cols = tuple(f"R{j}" for j in range(self.num_res))
        self.need_tree = ttk.Treeview(
            left, columns=("P",) + cols, show="headings", height=8)
        self.need_tree.heading("P", text="Process")
        self.need_tree.column("P", width=70, anchor="center")
        for c in cols:
            self.need_tree.heading(c, text=c)
            self.need_tree.column(c, width=50, anchor="center")
        self.need_tree.pack(fill="y")

        right = tk.Frame(lower, bg=Theme.BG)
        right.pack(side="left", fill="both", expand=True, padx=(16, 0))
        make_label(right, "Resource Allocation Graph", 11, bold=True,
                   bg=Theme.BG).pack(anchor="w", pady=(0, 4))
        self.canvas = tk.Canvas(right, bg=Theme.PANEL, highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)

    # ------------------------------------------------------------------ #
    def _rebuild(self):
        """Resize the grids to the requested dimensions (values reset to 0)."""
        try:
            p = int(self.proc_e.get())
            r = int(self.res_e.get())
            if p < 1 or r < 1:
                raise ValueError
        except ValueError:
            messagebox.showerror("Error", "Processes and resources must be "
                                          "positive integers.")
            return
        self.num_proc, self.num_res = p, r
        zeros = [[0] * r for _ in range(p)]
        self._populate_matrices(zeros, zeros, [0] * r)
        self._rebuild_need_columns()

    def _rebuild_need_columns(self):
        """Recreate the Need treeview columns for the current resource count."""
        self.need_tree.delete(*self.need_tree.get_children())
        cols = tuple(f"R{j}" for j in range(self.num_res))
        self.need_tree.configure(columns=("P",) + cols)
        self.need_tree.heading("P", text="Process")
        self.need_tree.column("P", width=70, anchor="center")
        for c in cols:
            self.need_tree.heading(c, text=c)
            self.need_tree.column(c, width=50, anchor="center")

    def _read_matrix(self, store):
        return [[int(e.get()) for e in row] for row in store]

    def _read_vector(self, store):
        return [int(e.get()) for e in store]

    def check(self):
        try:
            alloc = self._read_matrix(self.alloc_entries)
            mx = self._read_matrix(self.max_entries)
            avail = self._read_vector(self.avail_entries)
        except ValueError:
            messagebox.showerror("Error", "All cells must be integers.")
            return

        # Need must be non-negative for a valid Max >= Allocation system.
        need = bankers.need_matrix(alloc, mx)
        if any(v < 0 for row in need for v in row):
            messagebox.showerror("Error", "Max must be >= Allocation for every "
                                          "process/resource.")
            return

        safe, sequence = bankers.is_safe(alloc, mx, avail)
        self._show_need(need)

        if safe:
            seq = " -> ".join(f"P{i}" for i in sequence)
            self.result_lbl.config(text=f"Safe sequence: {seq}",
                                   fg=Theme.ACCENT_2)
            log(f"Deadlock check: SAFE ({seq})")
        else:
            self.result_lbl.config(text="DEADLOCK / unsafe state",
                                   fg=Theme.ACCENT_3)
            log("Deadlock check: UNSAFE state")

        # No requests in the avoidance view; show held allocations only.
        rag = bankers.build_rag(alloc, [[0] * self.num_res] * self.num_proc,
                                self.num_res)
        self._draw_rag(rag)

    def _show_need(self, need):
        self.need_tree.delete(*self.need_tree.get_children())
        for i, row in enumerate(need):
            self.need_tree.insert("", "end", values=(f"P{i}",) + tuple(row))

    def _draw_rag(self, rag):
        """Draw processes in a row, resources in a row below, with arrows."""
        c = self.canvas
        c.delete("all")
        c.update_idletasks()
        width = max(c.winfo_width(), 300)

        procs = rag["processes"]
        resources = rag["resources"]
        node_pos = {}
        radius = 18

        def spread(items, y):
            n = len(items)
            for k, name in enumerate(items):
                x = width * (k + 1) / (n + 1)
                node_pos[name] = (x, y)

        spread(procs, 70)
        spread(resources, 220)

        # Edges first so nodes sit on top.
        for src, dst in rag["edges"]:
            if src not in node_pos or dst not in node_pos:
                continue
            x0, y0 = node_pos[src]
            x1, y1 = node_pos[dst]
            c.create_line(x0, y0, x1, y1, fill=Theme.TEXT_DIM, width=2,
                          arrow="last", arrowshape=(12, 14, 5))

        for name in procs:
            x, y = node_pos[name]
            c.create_oval(x - radius, y - radius, x + radius, y + radius,
                          fill=Theme.ACCENT, outline=Theme.BG, width=2)
            c.create_text(x, y, text=name, fill="#1e2030",
                          font=(Theme.FONT, 9, "bold"))

        for name in resources:
            x, y = node_pos[name]
            c.create_rectangle(x - radius, y - radius, x + radius, y + radius,
                               fill=Theme.ACCENT_4, outline=Theme.BG, width=2)
            c.create_text(x, y, text=name, fill="#1e2030",
                          font=(Theme.FONT, 9, "bold"))
