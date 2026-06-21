"""apps/notepad.py - Notepad / Text Editor application.

Loads from and saves to data/notes.txt.
"""

import tkinter as tk
from tkinter import scrolledtext, messagebox, filedialog

from utils import Theme, make_button, center_window, NOTES_FILE
from core.logger import log


class NotepadApp(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.title("Notepad")
        self.configure(bg=Theme.BG)
        center_window(self, 560, 480)
        self.current_path = NOTES_FILE

        bar = tk.Frame(self, bg=Theme.BG)
        bar.pack(fill="x", padx=8, pady=8)
        make_button(bar, "Open", self.open_file,
                    bg=Theme.PANEL_LIGHT).pack(side="left", padx=3)
        make_button(bar, "Save", self.save,
                    bg=Theme.ACCENT_2).pack(side="left", padx=3)
        make_button(bar, "Save As", self.save_as,
                    bg=Theme.ACCENT).pack(side="left", padx=3)
        make_button(bar, "Clear", self.clear,
                    bg=Theme.ACCENT_3).pack(side="left", padx=3)

        self.text = scrolledtext.ScrolledText(
            self, bg=Theme.PANEL, fg=Theme.TEXT,
            insertbackground=Theme.TEXT, relief="flat",
            font=(Theme.FONT_MONO, 12), wrap="word", undo=True)
        self.text.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        self.status = tk.Label(self, text="", anchor="w",
                               bg=Theme.TASKBAR, fg=Theme.TEXT_DIM,
                               font=(Theme.FONT, 9))
        self.status.pack(fill="x")

        self._load(NOTES_FILE)

        log("Notepad opened")

    def _load(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                self.text.delete("1.0", "end")
                self.text.insert("1.0", f.read())
            self.current_path = path
            self.status.config(text=f"Loaded {path}")
        except FileNotFoundError:
            self.status.config(text="New file")

    def open_file(self):
        path = filedialog.askopenfilename(
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            self._load(path)

    def save(self):
        self._write(self.current_path)

    def save_as(self):
        path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")])
        if path:
            self._write(path)
            self.current_path = path

    def _write(self, path):
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.text.get("1.0", "end-1c"))
        self.status.config(text=f"Saved {path}")

    def clear(self):
        if messagebox.askyesno("Clear", "Clear all text?"):
            self.text.delete("1.0", "end")
