"""apps/ipc.py - Inter-Process Communication simulator GUI.

A thin Tkinter front-end over algorithms/ipc_algo.py. A ttk.Notebook offers
three tabs, each demonstrating one classic IPC mechanism:

  * Shared Memory - a row of slots; a writer process stores into a slot and a
    reader process reads it back, proving both share the same memory.
  * Message Queue - a producer sends messages, a consumer receives them FIFO;
    the live queue contents are shown.
  * Pipe          - text written into the pipe is consumed from the front by a
    reader, demonstrating stream semantics.

Every action is appended to an on-screen activity log and also recorded through
core.logger.log so it shows up in the kernel log window.
"""

import tkinter as tk
from tkinter import ttk, messagebox

from utils import (Theme, make_label, make_button, make_entry,
                   center_window)
from core.logger import log
from algorithms.ipc_algo import SharedMemory, MessageQueue, Pipe


class IPCApp(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.title("IPC Simulator")
        self.configure(bg=Theme.BG)
        center_window(self, 860, 680)
        log("IPC Simulator opened")

        # --- IPC backends (pure logic) -------------------------------- #
        self.shm = SharedMemory(size=8)
        self.mq = MessageQueue()
        self.pipe = Pipe()

        make_label(self, "Inter-Process Communication Simulator", 16,
                   bold=True, bg=Theme.BG).pack(pady=(14, 2))
        make_label(self, "Explore how processes talk: shared memory, message "
                         "queues and pipes.", 10, fg=Theme.TEXT_DIM,
                   bg=Theme.BG).pack()

        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, padx=16, pady=12)

        self._build_shared_memory_tab(nb)
        self._build_message_queue_tab(nb)
        self._build_pipe_tab(nb)
        self._build_activity_log()

        # Prefill tiny demos so nothing starts empty.
        self._seed_demos()

    # ================================================================== #
    # Shared Memory tab
    # ================================================================== #
    def _build_shared_memory_tab(self, nb):
        tab = tk.Frame(nb, bg=Theme.PANEL)
        nb.add(tab, text="Shared Memory")

        make_label(tab, "A single buffer shared by all processes. Whatever a "
                        "writer stores, a reader sees.", 10,
                   fg=Theme.TEXT_DIM).pack(anchor="w", padx=12, pady=(12, 8))

        # Row of slot cells.
        cells_wrap = tk.Frame(tab, bg=Theme.PANEL)
        cells_wrap.pack(padx=12, pady=4)
        self.shm_cells = []
        for i in range(self.shm.size):
            col = tk.Frame(cells_wrap, bg=Theme.PANEL)
            col.grid(row=0, column=i, padx=4)
            make_label(col, f"[{i}]", 9, fg=Theme.TEXT_DIM).pack()
            cell = tk.Label(col, text="-", width=6, height=2,
                            bg=Theme.PANEL_LIGHT, fg=Theme.TEXT,
                            font=(Theme.FONT_MONO, 11, "bold"),
                            relief="flat")
            cell.pack(pady=2)
            self.shm_cells.append(cell)

        # Writer controls.
        wbar = tk.Frame(tab, bg=Theme.PANEL)
        wbar.pack(fill="x", padx=12, pady=(14, 4))
        make_label(wbar, "Writer process -> slot:", 10).pack(side="left")
        self.shm_w_index = make_entry(wbar, width=4)
        self.shm_w_index.insert(0, "0")
        self.shm_w_index.pack(side="left", padx=6)
        make_label(wbar, "value:", 10).pack(side="left")
        self.shm_w_value = make_entry(wbar, width=14)
        self.shm_w_value.pack(side="left", padx=6)
        make_button(wbar, "Write", self._shm_write,
                    bg=Theme.ACCENT_2).pack(side="left", padx=6)

        # Reader controls.
        rbar = tk.Frame(tab, bg=Theme.PANEL)
        rbar.pack(fill="x", padx=12, pady=4)
        make_label(rbar, "Reader process <- slot:", 10).pack(side="left")
        self.shm_r_index = make_entry(rbar, width=4)
        self.shm_r_index.insert(0, "0")
        self.shm_r_index.pack(side="left", padx=6)
        make_button(rbar, "Read", self._shm_read,
                    bg=Theme.ACCENT).pack(side="left", padx=6)
        self.shm_read_lbl = make_label(rbar, "", 11, bold=True,
                                       fg=Theme.ACCENT_4)
        self.shm_read_lbl.pack(side="left", padx=12)

    def _shm_refresh(self):
        """Redraw every slot cell from the shared buffer."""
        for i, val in enumerate(self.shm.dump()):
            self.shm_cells[i].config(text="-" if val is None else str(val))

    def _shm_write(self):
        try:
            index = int(self.shm_w_index.get())
            value = self.shm_w_value.get().strip()
            if not value:
                raise ValueError("Enter a value to write.")
            self.shm.write(index, value)
        except (ValueError, IndexError) as e:
            messagebox.showerror("Shared Memory", str(e))
            return
        self._shm_refresh()
        self._activity(f"SHM: writer wrote '{value}' to slot {index}")
        log(f"IPC SharedMemory write slot {index} = {value}")

    def _shm_read(self):
        try:
            index = int(self.shm_r_index.get())
            value = self.shm.read(index)
        except (ValueError, IndexError) as e:
            messagebox.showerror("Shared Memory", str(e))
            return
        shown = "(empty)" if value is None else str(value)
        self.shm_read_lbl.config(text=f"slot {index} = {shown}")
        self._activity(f"SHM: reader read slot {index} -> {shown}")
        log(f"IPC SharedMemory read slot {index} -> {shown}")

    # ================================================================== #
    # Message Queue tab
    # ================================================================== #
    def _build_message_queue_tab(self, nb):
        tab = tk.Frame(nb, bg=Theme.PANEL)
        nb.add(tab, text="Message Queue")

        make_label(tab, "Asynchronous FIFO message passing. The consumer "
                        "receives messages in send order.", 10,
                   fg=Theme.TEXT_DIM).pack(anchor="w", padx=12, pady=(12, 8))

        sbar = tk.Frame(tab, bg=Theme.PANEL)
        sbar.pack(fill="x", padx=12, pady=4)
        make_label(sbar, "Producer message:", 10).pack(side="left")
        self.mq_entry = make_entry(sbar, width=24)
        self.mq_entry.pack(side="left", padx=6)
        make_button(sbar, "Send", self._mq_send,
                    bg=Theme.ACCENT_2).pack(side="left", padx=6)
        make_button(sbar, "Receive", self._mq_receive,
                    bg=Theme.ACCENT).pack(side="left", padx=6)

        self.mq_recv_lbl = make_label(tab, "", 11, bold=True,
                                      fg=Theme.ACCENT_4)
        self.mq_recv_lbl.pack(anchor="w", padx=12, pady=(4, 4))

        make_label(tab, "Queue (front -> back):", 10, bold=True).pack(
            anchor="w", padx=12, pady=(8, 2))
        self.mq_tree = ttk.Treeview(tab, columns=("pos", "msg"),
                                    show="headings", height=8)
        self.mq_tree.heading("pos", text="#")
        self.mq_tree.heading("msg", text="Message")
        self.mq_tree.column("pos", width=60, anchor="center")
        self.mq_tree.column("msg", width=600, anchor="w")
        self.mq_tree.pack(fill="both", expand=True, padx=12, pady=(0, 12))

    def _mq_refresh(self):
        """Redraw the queue Treeview from the live queue contents."""
        self.mq_tree.delete(*self.mq_tree.get_children())
        for pos, msg in enumerate(self.mq.peek()):
            self.mq_tree.insert("", "end", values=(pos, msg))

    def _mq_send(self):
        msg = self.mq_entry.get().strip()
        if not msg:
            messagebox.showerror("Message Queue", "Enter a message to send.")
            return
        self.mq.send(msg)
        self.mq_entry.delete(0, "end")
        self._mq_refresh()
        self._activity(f"MQ: producer sent '{msg}'")
        log(f"IPC MessageQueue send '{msg}'")

    def _mq_receive(self):
        msg = self.mq.receive()
        if msg is None:
            self.mq_recv_lbl.config(text="Received: (queue empty)")
            self._activity("MQ: consumer receive -> queue empty")
            log("IPC MessageQueue receive -> empty")
            return
        self.mq_recv_lbl.config(text=f"Received: {msg}")
        self._mq_refresh()
        self._activity(f"MQ: consumer received '{msg}'")
        log(f"IPC MessageQueue receive -> '{msg}'")

    # ================================================================== #
    # Pipe tab
    # ================================================================== #
    def _build_pipe_tab(self, nb):
        tab = tk.Frame(nb, bg=Theme.PANEL)
        nb.add(tab, text="Pipe")

        make_label(tab, "A unidirectional stream. Reading consumes characters "
                        "from the front of the buffer.", 10,
                   fg=Theme.TEXT_DIM).pack(anchor="w", padx=12, pady=(12, 8))

        wbar = tk.Frame(tab, bg=Theme.PANEL)
        wbar.pack(fill="x", padx=12, pady=4)
        make_label(wbar, "Write to pipe:", 10).pack(side="left")
        self.pipe_entry = make_entry(wbar, width=28)
        self.pipe_entry.pack(side="left", padx=6)
        make_button(wbar, "Write", self._pipe_write,
                    bg=Theme.ACCENT_2).pack(side="left", padx=6)

        rbar = tk.Frame(tab, bg=Theme.PANEL)
        rbar.pack(fill="x", padx=12, pady=4)
        make_label(rbar, "Read", 10).pack(side="left")
        self.pipe_n = make_entry(rbar, width=5)
        self.pipe_n.pack(side="left", padx=6)
        make_label(rbar, "chars (blank = all):", 10).pack(side="left")
        make_button(rbar, "Read", self._pipe_read,
                    bg=Theme.ACCENT).pack(side="left", padx=6)

        self.pipe_state_lbl = make_label(tab, "", 11, bold=True)
        self.pipe_state_lbl.pack(anchor="w", padx=12, pady=(8, 2))
        self.pipe_read_lbl = make_label(tab, "", 11, bold=True,
                                        fg=Theme.ACCENT_4)
        self.pipe_read_lbl.pack(anchor="w", padx=12, pady=(2, 2))

        make_label(tab, "Buffer contents:", 10, bold=True).pack(
            anchor="w", padx=12, pady=(8, 2))
        self.pipe_buf = tk.Text(tab, height=6, bg=Theme.PANEL_LIGHT,
                                fg=Theme.TEXT, relief="flat",
                                font=(Theme.FONT_MONO, 11),
                                insertbackground=Theme.TEXT)
        self.pipe_buf.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.pipe_buf.config(state="disabled")

    def _pipe_refresh(self):
        """Update the buffer display and remaining-count label."""
        remaining = self.pipe.available()
        contents = self.pipe.read(remaining)  # drain...
        self.pipe.write(contents)             # ...and restore (peek workaround)
        self.pipe_state_lbl.config(text=f"Remaining in pipe: {remaining} char(s)")
        self.pipe_buf.config(state="normal")
        self.pipe_buf.delete("1.0", "end")
        self.pipe_buf.insert("1.0", contents)
        self.pipe_buf.config(state="disabled")

    def _pipe_write(self):
        data = self.pipe_entry.get()
        if not data:
            messagebox.showerror("Pipe", "Enter text to write.")
            return
        self.pipe.write(data)
        self.pipe_entry.delete(0, "end")
        self._pipe_refresh()
        self._activity(f"Pipe: wrote '{data}' ({len(data)} char(s))")
        log(f"IPC Pipe write '{data}'")

    def _pipe_read(self):
        raw = self.pipe_n.get().strip()
        try:
            n = int(raw) if raw else None
            data = self.pipe.read(n)
        except ValueError as e:
            messagebox.showerror("Pipe", str(e))
            return
        shown = data if data else "(nothing to read)"
        self.pipe_read_lbl.config(text=f"Read: {shown}")
        self._pipe_refresh()
        self._activity(f"Pipe: read -> '{data}'")
        log(f"IPC Pipe read -> '{data}'")

    # ================================================================== #
    # Activity log (shared by all tabs)
    # ================================================================== #
    def _build_activity_log(self):
        make_label(self, "Activity Log", 11, bold=True, bg=Theme.BG).pack(
            anchor="w", padx=16)
        self.activity = tk.Text(self, height=6, bg=Theme.PANEL,
                                fg=Theme.TEXT, relief="flat",
                                font=(Theme.FONT_MONO, 10))
        self.activity.pack(fill="x", padx=16, pady=(2, 14))
        self.activity.config(state="disabled")

    def _activity(self, text):
        """Append a line to the on-screen activity log."""
        self.activity.config(state="normal")
        self.activity.insert("end", text + "\n")
        self.activity.see("end")
        self.activity.config(state="disabled")

    # ================================================================== #
    # Demo seeding
    # ================================================================== #
    def _seed_demos(self):
        """Prefill each mechanism with a tiny demo so nothing is empty."""
        self.shm.write(0, "hello")
        self.shm.write(1, "42")
        self._shm_refresh()

        self.mq.send("ping")
        self.mq.send("pong")
        self._mq_refresh()

        self.pipe.write("stream")
        self._pipe_refresh()

        self._activity("Seeded demo data for all three mechanisms.")
