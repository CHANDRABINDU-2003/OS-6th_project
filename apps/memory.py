"""apps/memory.py - Memory Management GUI.

Thin Tkinter front-end over algorithms/memory_algorithms.py. A Notebook with
two tabs:

  * Contiguous Allocation - First / Best / Worst Fit, an allocation table and a
    Canvas memory map, plus internal / external fragmentation.
  * Paging - logical-to-physical address translation with a page-table editor
    and a Canvas visualisation of pages mapped to frames.

Follows the reference app pattern (apps/scheduler.py): subclass tk.Toplevel,
log launch, build UI from the utils widget factories + Theme.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from utils import (Theme, make_label, make_button, make_entry,
                   center_window, color_for)
from core.logger import log
from algorithms import memory_algorithms as mem


class MemoryApp(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.title("Memory Manager")
        self.configure(bg=Theme.BG)
        center_window(self, 900, 700)
        log("Memory Manager opened")

        make_label(self, "Memory Management Simulator", 16, bold=True,
                   bg=Theme.BG).pack(pady=(14, 2))
        make_label(self, "Contiguous allocation and paging address translation.",
                   10, fg=Theme.TEXT_DIM, bg=Theme.BG).pack()

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=14)

        self.alloc_tab = tk.Frame(nb, bg=Theme.BG)
        self.paging_tab = tk.Frame(nb, bg=Theme.BG)
        nb.add(self.alloc_tab, text="Contiguous Allocation")
        nb.add(self.paging_tab, text="Paging")

        self._build_alloc_tab()
        self._build_paging_tab()

    # ================================================================== #
    # Tab 1 - Contiguous Allocation
    # ================================================================== #
    def _build_alloc_tab(self):
        t = self.alloc_tab

        inp = tk.Frame(t, bg=Theme.PANEL)
        inp.pack(fill="x", padx=8, pady=10)

        make_label(inp, "Block sizes (comma separated):", 10, bold=True).grid(
            row=0, column=0, sticky="w", padx=10, pady=(10, 2))
        self.blocks_e = make_entry(inp, width=40)
        self.blocks_e.insert(0, "100, 500, 200, 300, 600")
        self.blocks_e.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))

        make_label(inp, "Process sizes (comma separated):", 10, bold=True).grid(
            row=2, column=0, sticky="w", padx=10, pady=(2, 2))
        self.procs_e = make_entry(inp, width=40)
        self.procs_e.insert(0, "212, 417, 112, 426")
        self.procs_e.grid(row=3, column=0, sticky="w", padx=10, pady=(0, 10))

        ctrl = tk.Frame(t, bg=Theme.BG)
        ctrl.pack(fill="x", padx=8)
        make_label(ctrl, "Strategy:", 10, bg=Theme.BG).pack(
            side="left", padx=(2, 6))
        self.strategy = tk.StringVar(value="First Fit")
        ttk.Combobox(ctrl, textvariable=self.strategy, state="readonly",
                     width=16,
                     values=["First Fit", "Best Fit", "Worst Fit"]).pack(
            side="left")
        make_button(ctrl, "Run Allocation", self.run_allocation,
                    bg=Theme.ACCENT_2).pack(side="right")

        self.alloc_tree = ttk.Treeview(
            t, columns=("proc", "size", "block"), show="headings", height=6)
        for c, txt, w in (("proc", "Process", 140),
                          ("size", "Size", 140),
                          ("block", "Block #", 220)):
            self.alloc_tree.heading(c, text=txt)
            self.alloc_tree.column(c, width=w, anchor="center")
        self.alloc_tree.pack(fill="x", padx=8, pady=(12, 6))

        self.frag_lbl = make_label(t, "", 11, bold=True, bg=Theme.BG)
        self.frag_lbl.pack()

        make_label(t, "Memory Map", 11, bold=True, bg=Theme.BG).pack(
            pady=(8, 2))
        self.mem_canvas = tk.Canvas(t, height=120, bg=Theme.PANEL,
                                    highlightthickness=0)
        self.mem_canvas.pack(fill="x", padx=8, pady=(0, 14))

    def _parse_ints(self, text, label):
        """Parse a comma/space separated list of positive ints."""
        parts = [p.strip() for p in text.replace(",", " ").split()]
        values = []
        for p in parts:
            if not p:
                continue
            try:
                n = int(p)
            except ValueError:
                raise ValueError(f"Invalid number in {label}: '{p}'.")
            if n <= 0:
                raise ValueError(f"{label} values must be positive.")
            values.append(n)
        if not values:
            raise ValueError(f"Enter at least one value for {label}.")
        return values

    def run_allocation(self):
        try:
            blocks = self._parse_ints(self.blocks_e.get(), "block sizes")
            processes = self._parse_ints(self.procs_e.get(), "process sizes")
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        strat = self.strategy.get()
        if strat == "First Fit":
            allocation = mem.first_fit(blocks, processes)
        elif strat == "Best Fit":
            allocation = mem.best_fit(blocks, processes)
        else:
            allocation = mem.worst_fit(blocks, processes)

        log(f"Memory allocation ran {strat} on {len(processes)} processes")
        self._show_allocation(blocks, processes, allocation, strat)

    def _show_allocation(self, blocks, processes, allocation, strat):
        self.alloc_tree.delete(*self.alloc_tree.get_children())
        for i, size in enumerate(processes):
            blk = allocation[i]
            cell = f"Block {blk}" if blk != -1 else "Not Allocated"
            self.alloc_tree.insert("", "end",
                                   values=(f"P{i + 1}", size, cell))

        frag = mem.fragmentation(blocks, processes, allocation)
        placed = sum(1 for a in allocation if a != -1)
        self.frag_lbl.config(
            text=(f"{strat}:  {placed}/{len(processes)} placed     "
                  f"Internal fragmentation: {frag['internal']}     "
                  f"External fragmentation: {frag['external']}"))
        self._draw_memory_map(blocks, processes, allocation)

    def _draw_memory_map(self, blocks, processes, allocation):
        c = self.mem_canvas
        c.delete("all")
        c.update_idletasks()

        # Group processes by the block they were placed in (in process order).
        per_block = {j: [] for j in range(len(blocks))}
        for i, blk in enumerate(allocation):
            if blk != -1:
                per_block[blk].append(i)

        margin = 20
        gap = 10
        width = max(c.winfo_width(), 200) - 2 * margin
        n = len(blocks)
        block_w = (width - gap * (n - 1)) / n if n else width

        max_block = max(blocks) if blocks else 1
        top, bottom = 25, 100

        x = margin
        for j, total in enumerate(blocks):
            scale = (bottom - top) / max_block
            # Outline of the whole block.
            c.create_rectangle(x, top, x + block_w, bottom,
                               outline=Theme.TEXT_DIM, width=1)
            c.create_text(x + block_w / 2, top - 10,
                          text=f"Blk {j} ({total})",
                          fill=Theme.TEXT, font=(Theme.FONT, 8, "bold"))

            # Stack the processes that live in this block from the bottom up.
            y = bottom
            for pid in per_block[j]:
                h = processes[pid] * scale
                c.create_rectangle(x, y - h, x + block_w, y,
                                   fill=color_for(pid), outline=Theme.BG,
                                   width=1)
                if h > 12:
                    c.create_text(x + block_w / 2, y - h / 2,
                                  text=f"P{pid + 1}", fill="#1e2030",
                                  font=(Theme.FONT, 8, "bold"))
                y -= h

            # Free tail of the block.
            c.create_text(x + block_w / 2, bottom + 12,
                          text="free" if not per_block[j] else "",
                          fill=Theme.TEXT_DIM, font=(Theme.FONT, 8))
            x += block_w + gap

    # ================================================================== #
    # Tab 2 - Paging
    # ================================================================== #
    def _build_paging_tab(self):
        t = self.paging_tab

        inp = tk.Frame(t, bg=Theme.PANEL)
        inp.pack(fill="x", padx=8, pady=10)

        make_label(inp, "Page size:", 10, bold=True).grid(
            row=0, column=0, sticky="w", padx=10, pady=(10, 6))
        self.page_size_e = make_entry(inp, width=10)
        self.page_size_e.insert(0, "100")
        self.page_size_e.grid(row=0, column=1, sticky="w", padx=10,
                              pady=(10, 6))

        make_label(inp, "Page table (page:frame, comma separated):",
                   10, bold=True).grid(row=1, column=0, columnspan=2,
                                       sticky="w", padx=10, pady=(2, 2))
        self.page_table_e = make_entry(inp, width=44)
        self.page_table_e.insert(0, "0:5, 1:2, 2:7, 3:1")
        self.page_table_e.grid(row=2, column=0, columnspan=2, sticky="w",
                               padx=10, pady=(0, 8))

        make_label(inp, "Logical address:", 10, bold=True).grid(
            row=3, column=0, sticky="w", padx=10, pady=(2, 10))
        self.logical_e = make_entry(inp, width=10)
        self.logical_e.insert(0, "250")
        self.logical_e.grid(row=3, column=1, sticky="w", padx=10,
                            pady=(2, 10))

        ctrl = tk.Frame(t, bg=Theme.BG)
        ctrl.pack(fill="x", padx=8)
        make_button(ctrl, "Translate", self.run_translate,
                    bg=Theme.ACCENT_2).pack(side="right")

        self.translate_lbl = make_label(t, "", 12, bold=True, bg=Theme.BG)
        self.translate_lbl.pack(pady=(12, 6))

        self.detail_tree = ttk.Treeview(
            t, columns=("field", "value"), show="headings", height=5)
        self.detail_tree.heading("field", text="Field")
        self.detail_tree.heading("value", text="Value")
        self.detail_tree.column("field", width=200, anchor="w")
        self.detail_tree.column("value", width=200, anchor="w")
        self.detail_tree.pack(fill="x", padx=8, pady=(0, 6))

        make_label(t, "Page -> Frame Map", 11, bold=True, bg=Theme.BG).pack(
            pady=(8, 2))
        self.page_canvas = tk.Canvas(t, height=180, bg=Theme.PANEL,
                                     highlightthickness=0)
        self.page_canvas.pack(fill="x", padx=8, pady=(0, 14))

    def _parse_page_table(self, text):
        """Parse 'page:frame, page:frame' into a {int: int} dict."""
        table = {}
        for part in text.split(","):
            part = part.strip()
            if not part:
                continue
            if ":" not in part:
                raise ValueError(f"Bad page-table entry: '{part}' "
                                 "(use page:frame).")
            page_s, frame_s = part.split(":", 1)
            try:
                page = int(page_s.strip())
                frame = int(frame_s.strip())
            except ValueError:
                raise ValueError(f"Bad page-table entry: '{part}'.")
            if page < 0 or frame < 0:
                raise ValueError("Page and frame numbers must be >= 0.")
            table[page] = frame
        return table

    def run_translate(self):
        try:
            page_size = int(self.page_size_e.get())
            if page_size <= 0:
                raise ValueError("Page size must be a positive integer.")
            logical = int(self.logical_e.get())
            if logical < 0:
                raise ValueError("Logical address must be >= 0.")
            page_table = self._parse_page_table(self.page_table_e.get())
        except ValueError as e:
            messagebox.showerror("Error", str(e))
            return

        result = mem.translate(logical, page_size, page_table)
        log(f"Paging translated address {logical} "
            f"({'fault' if result['fault'] else 'hit'})")
        self._show_translation(logical, page_size, page_table, result)

    def _show_translation(self, logical, page_size, page_table, result):
        if result["fault"]:
            self.translate_lbl.config(text="PAGE FAULT",
                                      fg=Theme.ACCENT_3)
            phys = "PAGE FAULT"
            frame = "-"
        else:
            self.translate_lbl.config(
                text=f"Logical {logical}  ->  Physical "
                     f"{result['physical_address']}", fg=Theme.ACCENT_2)
            phys = result["physical_address"]
            frame = result["frame"]

        self.detail_tree.delete(*self.detail_tree.get_children())
        for field, value in (
                ("Logical address", logical),
                ("Page number", result["page"]),
                ("Offset", result["offset"]),
                ("Frame number", frame),
                ("Physical address", phys)):
            self.detail_tree.insert("", "end", values=(field, value))

        self._draw_page_map(page_table, result)

    def _draw_page_map(self, page_table, result):
        c = self.page_canvas
        c.delete("all")
        c.update_idletasks()

        if not page_table:
            c.create_text(20, 20, text="(empty page table)",
                          anchor="w", fill=Theme.TEXT_DIM,
                          font=(Theme.FONT, 10))
            return

        margin = 30
        box_w, box_h, vgap = 70, 26, 6
        left_x = margin
        right_x = max(c.winfo_width(), 300) - margin - box_w
        y = 12
        active_page = result["page"]

        for page in sorted(page_table):
            frame = page_table[page]
            hit = (page == active_page and not result["fault"])
            page_fill = Theme.ACCENT if hit else Theme.PANEL_LIGHT
            frame_fill = color_for(frame)

            c.create_rectangle(left_x, y, left_x + box_w, y + box_h,
                               fill=page_fill, outline=Theme.TEXT_DIM)
            c.create_text(left_x + box_w / 2, y + box_h / 2,
                          text=f"Page {page}", fill=Theme.TEXT,
                          font=(Theme.FONT, 9, "bold"))

            c.create_rectangle(right_x, y, right_x + box_w, y + box_h,
                               fill=frame_fill, outline=Theme.TEXT_DIM)
            c.create_text(right_x + box_w / 2, y + box_h / 2,
                          text=f"Frame {frame}", fill="#1e2030",
                          font=(Theme.FONT, 9, "bold"))

            arrow_color = Theme.ACCENT_2 if hit else Theme.TEXT_DIM
            c.create_line(left_x + box_w, y + box_h / 2,
                          right_x, y + box_h / 2,
                          fill=arrow_color, arrow="last",
                          width=2 if hit else 1)
            y += box_h + vgap
