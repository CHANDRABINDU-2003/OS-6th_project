"""apps/shell.py - Command Line Shell.

A simulated terminal that operates on the same virtual file system stored in
data/disk.json. Supports a small but useful set of Unix-like commands.

Shares data/disk.json with the File System app so changes propagate both ways.
"""

import os
import time
import tkinter as tk

from utils import Theme, center_window, read_json, write_json, DISK_FILE
from core.logger import log


HELP_TEXT = """Available commands:
  help              Show this help
  ls                List items in the current directory
  cd <dir>          Change directory (use '..' to go up)
  pwd               Print working directory
  cat <file>        Show a file's contents
  mkdir <name>      Create a folder
  touch <name>      Create an empty file
  echo <text>       Print text
  date              Show current date/time
  whoami            Show current user
  clear             Clear the screen
  exit              Close the shell
"""


class ShellApp(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.title("Shell")
        self.configure(bg="#0b0b12")
        center_window(self, 720, 460)

        self.disk = self._load_disk()
        self.path = [self.disk]  # stack of folder nodes; path[-1] is cwd

        self.output = tk.Text(self, bg="#0b0b12", fg="#9ece6a",
                              insertbackground="#9ece6a", relief="flat",
                              font=(Theme.FONT_MONO, 11), wrap="word")
        self.output.pack(fill="both", expand=True, padx=8, pady=(8, 0))
        self.output.config(state="disabled")

        entry_row = tk.Frame(self, bg="#0b0b12")
        entry_row.pack(fill="x", padx=8, pady=8)
        self.prompt_lbl = tk.Label(entry_row, text=self._prompt(),
                                   bg="#0b0b12", fg="#7aa2f7",
                                   font=(Theme.FONT_MONO, 11))
        self.prompt_lbl.pack(side="left")
        self.entry = tk.Entry(entry_row, bg="#0b0b12", fg="#c0caf5",
                              insertbackground="#c0caf5", relief="flat",
                              font=(Theme.FONT_MONO, 11))
        self.entry.pack(side="left", fill="x", expand=True)
        self.entry.bind("<Return>", self._on_enter)
        self.entry.focus_set()

        self._println("MiniOS Shell — type 'help' to get started.\n")
        log("Shell opened")

    # ------------------------------------------------------------------ #
    # Disk
    # ------------------------------------------------------------------ #
    def _load_disk(self):
        data = read_json(DISK_FILE, default=None)
        if isinstance(data, dict) and data:
            return data
        return {"type": "folder", "name": "root", "children": []}

    def _save_disk(self):
        write_json(DISK_FILE, self.disk)

    # ------------------------------------------------------------------ #
    # Output helpers
    # ------------------------------------------------------------------ #
    def _prompt(self):
        path = "/".join(n["name"] for n in self.path)
        return f"{path} $ "

    def _println(self, text=""):
        self.output.config(state="normal")
        self.output.insert("end", text + "\n")
        self.output.see("end")
        self.output.config(state="disabled")

    def _on_enter(self, _event):
        cmd = self.entry.get().strip()
        self.entry.delete(0, "end")
        self._println(self._prompt() + cmd)
        if cmd:
            self._run(cmd)
        self.prompt_lbl.config(text=self._prompt())

    # ------------------------------------------------------------------ #
    # Command dispatch
    # ------------------------------------------------------------------ #
    def _run(self, line):
        parts = line.split()
        cmd, args = parts[0], parts[1:]
        cwd = self.path[-1]

        if cmd == "help":
            self._println(HELP_TEXT)
        elif cmd == "ls":
            items = cwd.get("children", [])
            if not items:
                self._println("(empty)")
            for c in items:
                tag = "/" if c["type"] == "folder" else ""
                self._println("  " + c["name"] + tag)
        elif cmd == "pwd":
            self._println("/" + "/".join(n["name"] for n in self.path))
        elif cmd == "cd":
            self._cd(args)
        elif cmd == "cat":
            self._cat(args)
        elif cmd == "mkdir":
            self._create(args, "folder")
        elif cmd == "touch":
            self._create(args, "file")
        elif cmd == "echo":
            self._println(" ".join(args))
        elif cmd == "date":
            self._println(time.strftime("%a %d %b %Y  %H:%M:%S"))
        elif cmd == "whoami":
            self._println(os.environ.get("USER", "user") + "@minios")
        elif cmd == "clear":
            self.output.config(state="normal")
            self.output.delete("1.0", "end")
            self.output.config(state="disabled")
        elif cmd == "exit":
            log("Shell closed")
            self.destroy()
        else:
            self._println(f"{cmd}: command not found")

    def _find(self, name, kind=None):
        for c in self.path[-1].get("children", []):
            if c["name"] == name and (kind is None or c["type"] == kind):
                return c
        return None

    def _cd(self, args):
        if not args:
            self._println("cd: missing operand")
            return
        target = args[0]
        if target == "..":
            if len(self.path) > 1:
                self.path.pop()
            return
        if target in ("/", "root"):
            self.path = [self.disk]
            return
        node = self._find(target, "folder")
        if node:
            self.path.append(node)
        else:
            self._println(f"cd: {target}: no such directory")

    def _cat(self, args):
        if not args:
            self._println("cat: missing operand")
            return
        node = self._find(args[0], "file")
        if node:
            self._println(node.get("content", ""))
        else:
            self._println(f"cat: {args[0]}: no such file")

    def _create(self, args, kind):
        if not args:
            self._println(f"{'mkdir' if kind == 'folder' else 'touch'}: missing operand")
            return
        name = args[0]
        if self._find(name):
            self._println(f"{name}: already exists")
            return
        node = ({"type": "folder", "name": name, "children": []}
                if kind == "folder"
                else {"type": "file", "name": name, "content": ""})
        self.path[-1].setdefault("children", []).append(node)
        self._save_disk()
