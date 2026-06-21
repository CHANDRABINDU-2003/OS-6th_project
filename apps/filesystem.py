"""apps/filesystem.py - Virtual File System.

A simple hierarchical file system (folders + text files) stored as JSON in
data/disk.json. Supports creating folders/files, editing file contents, and
deleting nodes. Demonstrates a tree-structured directory layout.

Shares data/disk.json with the Shell so changes in one show up in the other.
"""

import tkinter as tk
from tkinter import ttk, simpledialog, messagebox, scrolledtext

from utils import (Theme, make_label, make_button, center_window,
                   read_json, write_json, DISK_FILE)
from core.logger import log


def _new_node(kind, name):
    if kind == "folder":
        return {"type": "folder", "name": name, "children": []}
    return {"type": "file", "name": name, "content": ""}


def _default_disk():
    root = _new_node("folder", "root")
    docs = _new_node("folder", "documents")
    docs["children"].append(
        {"type": "file", "name": "readme.txt",
         "content": "This is a virtual file inside MiniOS."})
    root["children"] = [docs, _new_node("folder", "system")]
    return root


class FileSystemApp(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.title("Virtual File System")
        self.configure(bg=Theme.BG)
        center_window(self, 760, 560)

        self.disk = self._load()
        # Map Treeview item id -> node dict
        self.node_map = {}

        self._build_ui()
        self._refresh_tree()
        log("Files opened")

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #
    def _load(self):
        data = read_json(DISK_FILE, default=None)
        if isinstance(data, dict) and data:
            return data
        return _default_disk()

    def _save(self):
        write_json(DISK_FILE, self.disk)

    # ------------------------------------------------------------------ #
    # UI
    # ------------------------------------------------------------------ #
    def _build_ui(self):
        make_label(self, "Virtual File System", 16, bold=True,
                   bg=Theme.BG).pack(pady=(14, 6))

        bar = tk.Frame(self, bg=Theme.BG)
        bar.pack(fill="x", padx=16)
        make_button(bar, "New Folder", self.new_folder,
                    bg=Theme.PANEL_LIGHT).pack(side="left", padx=3)
        make_button(bar, "New File", self.new_file,
                    bg=Theme.PANEL_LIGHT).pack(side="left", padx=3)
        make_button(bar, "Open", self.open_file,
                    bg=Theme.ACCENT).pack(side="left", padx=3)
        make_button(bar, "Delete", self.delete_node,
                    bg=Theme.ACCENT_3).pack(side="left", padx=3)

        body = tk.Frame(self, bg=Theme.BG)
        body.pack(fill="both", expand=True, padx=16, pady=12)

        self.tree = ttk.Treeview(body, show="tree", selectmode="browse")
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<Double-1>", lambda e: self.open_file())

        scroll = ttk.Scrollbar(body, orient="vertical",
                               command=self.tree.yview)
        scroll.pack(side="left", fill="y")
        self.tree.configure(yscrollcommand=scroll.set)

    # ------------------------------------------------------------------ #
    # Tree rendering
    # ------------------------------------------------------------------ #
    def _refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        self.node_map.clear()
        self._insert_node("", self.disk)
        # Expand the root.
        for iid in self.tree.get_children():
            self.tree.item(iid, open=True)

    def _insert_node(self, parent_iid, node):
        icon = "📁 " if node["type"] == "folder" else "📄 "
        iid = self.tree.insert(parent_iid, "end", text=icon + node["name"])
        self.node_map[iid] = node
        if node["type"] == "folder":
            for child in node["children"]:
                self._insert_node(iid, child)

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #
    def _selected(self):
        sel = self.tree.selection()
        return self.node_map.get(sel[0]) if sel else None

    def _target_folder(self):
        """Folder to create inside: the selection if it's a folder, else root."""
        node = self._selected()
        if node and node["type"] == "folder":
            return node
        return self.disk

    def _find_parent(self, target, current=None):
        current = current or self.disk
        for child in current.get("children", []):
            if child is target:
                return current
            if child["type"] == "folder":
                found = self._find_parent(target, child)
                if found:
                    return found
        return None

    # ------------------------------------------------------------------ #
    # Actions
    # ------------------------------------------------------------------ #
    def new_folder(self):
        name = simpledialog.askstring("New Folder", "Folder name:", parent=self)
        if name:
            self._target_folder()["children"].append(_new_node("folder", name))
            self._save()
            self._refresh_tree()

    def new_file(self):
        name = simpledialog.askstring("New File", "File name:", parent=self)
        if name:
            self._target_folder()["children"].append(_new_node("file", name))
            self._save()
            self._refresh_tree()

    def open_file(self):
        node = self._selected()
        if not node or node["type"] != "file":
            messagebox.showinfo("Open", "Select a file to open.")
            return
        FileEditor(self, node, on_save=self._save)

    def delete_node(self):
        node = self._selected()
        if not node:
            return
        if node is self.disk:
            messagebox.showwarning("Delete", "Cannot delete the root.")
            return
        if messagebox.askyesno("Delete", f"Delete '{node['name']}'?"):
            parent = self._find_parent(node)
            if parent:
                parent["children"].remove(node)
                self._save()
                self._refresh_tree()


class FileEditor(tk.Toplevel):
    """A small editor window for a single virtual file."""

    def __init__(self, parent, node, on_save):
        super().__init__(parent)
        self.node = node
        self.on_save = on_save
        self.title(f"Edit - {node['name']}")
        self.configure(bg=Theme.BG)
        center_window(self, 480, 380)

        self.text = scrolledtext.ScrolledText(
            self, bg=Theme.PANEL, fg=Theme.TEXT,
            insertbackground=Theme.TEXT, relief="flat",
            font=(Theme.FONT_MONO, 11), wrap="word")
        self.text.pack(fill="both", expand=True, padx=10, pady=10)
        self.text.insert("1.0", node.get("content", ""))

        make_button(self, "Save", self.save, bg=Theme.ACCENT_2).pack(
            pady=(0, 10))

    def save(self):
        self.node["content"] = self.text.get("1.0", "end-1c")
        self.on_save()
        messagebox.showinfo("Saved", "File saved to virtual disk.")
