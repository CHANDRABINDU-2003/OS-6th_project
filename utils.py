"""utils.py - Shared theme system, widget factories, paths and data helpers.

Every module imports from here so the whole simulator shares one look-and-feel.
The Theme class holds the *active* palette; ThemeManager swaps palettes at
runtime (see the Theme Manager app). Windows opened after a theme change pick
up the new colours.
"""

import os
import json
import tkinter as tk

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
ASSETS_DIR = os.path.join(BASE_DIR, "assets")

DISK_FILE = os.path.join(DATA_DIR, "disk.json")
NOTES_FILE = os.path.join(DATA_DIR, "notes.txt")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PROCESSES_FILE = os.path.join(DATA_DIR, "processes.json")
LOGS_FILE = os.path.join(DATA_DIR, "logs.txt")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")


# --------------------------------------------------------------------------- #
# Themes
# --------------------------------------------------------------------------- #
THEMES = {
    "Aurora": {
        "BG": "#070B17", "PANEL": "#121826", "PANEL_LIGHT": "#1B2236",
        "ACCENT": "#6C63FF", "ACCENT_2": "#32D583", "ACCENT_3": "#FF5E6C",
        "ACCENT_4": "#FBBF24", "TEXT": "#EAEAEA", "TEXT_DIM": "#98A6C0",
        "TASKBAR": "#0A0E1A",
    },
    "Midnight": {
        "BG": "#1e2030", "PANEL": "#2a2d43", "PANEL_LIGHT": "#363a54",
        "ACCENT": "#7aa2f7", "ACCENT_2": "#9ece6a", "ACCENT_3": "#f7768e",
        "ACCENT_4": "#e0af68", "TEXT": "#c0caf5", "TEXT_DIM": "#7f87b3",
        "TASKBAR": "#16161e",
    },
    "Light": {
        "BG": "#eceff4", "PANEL": "#ffffff", "PANEL_LIGHT": "#e2e6ee",
        "ACCENT": "#3b82f6", "ACCENT_2": "#16a34a", "ACCENT_3": "#dc2626",
        "ACCENT_4": "#d97706", "TEXT": "#1f2937", "TEXT_DIM": "#6b7280",
        "TASKBAR": "#d8dee9",
    },
    "Matrix": {
        "BG": "#020c02", "PANEL": "#0b1a0b", "PANEL_LIGHT": "#123012",
        "ACCENT": "#39ff14", "ACCENT_2": "#7CFC00", "ACCENT_3": "#ff5555",
        "ACCENT_4": "#caff70", "TEXT": "#b9ffb9", "TEXT_DIM": "#5fa55f",
        "TASKBAR": "#010801",
    },
    "Dracula": {
        "BG": "#282a36", "PANEL": "#343746", "PANEL_LIGHT": "#44475a",
        "ACCENT": "#bd93f9", "ACCENT_2": "#50fa7b", "ACCENT_3": "#ff5555",
        "ACCENT_4": "#ffb86c", "TEXT": "#f8f8f2", "TEXT_DIM": "#9aa0b5",
        "TASKBAR": "#1d1e26",
    },
}


class Theme:
    """Active palette. Mutated in place by ThemeManager.apply()."""
    name = "Aurora"
    BG = THEMES["Aurora"]["BG"]
    PANEL = THEMES["Aurora"]["PANEL"]
    PANEL_LIGHT = THEMES["Aurora"]["PANEL_LIGHT"]
    ACCENT = THEMES["Aurora"]["ACCENT"]
    ACCENT_2 = THEMES["Aurora"]["ACCENT_2"]
    ACCENT_3 = THEMES["Aurora"]["ACCENT_3"]
    ACCENT_4 = THEMES["Aurora"]["ACCENT_4"]
    TEXT = THEMES["Aurora"]["TEXT"]
    TEXT_DIM = THEMES["Aurora"]["TEXT_DIM"]
    TASKBAR = THEMES["Aurora"]["TASKBAR"]

    FONT = "Helvetica"
    FONT_MONO = "Courier"


class ThemeManager:
    """Swaps the active palette and notifies subscribers (e.g. the desktop)."""
    _subscribers = []

    @classmethod
    def subscribe(cls, callback):
        cls._subscribers.append(callback)

    @classmethod
    def unsubscribe(cls, callback):
        if callback in cls._subscribers:
            cls._subscribers.remove(callback)

    @classmethod
    def apply(cls, name):
        if name not in THEMES:
            return
        palette = THEMES[name]
        Theme.name = name
        for key, value in palette.items():
            setattr(Theme, key, value)
        save_settings({"theme": name})
        for cb in list(cls._subscribers):
            try:
                cb()
            except tk.TclError:
                pass  # widget was destroyed

    @classmethod
    def load_saved(cls):
        name = load_settings().get("theme", "Aurora")
        if name in THEMES and name != Theme.name:
            cls.apply(name)


# A reusable colour wheel for Gantt charts, memory blocks, graphs, etc.
PALETTE = ["#7aa2f7", "#9ece6a", "#f7768e", "#e0af68",
           "#bb9af7", "#7dcfff", "#ff9e64", "#73daca",
           "#c0caf5", "#b4f9f8"]


def color_for(index):
    """Return a stable colour from the palette for a given integer index."""
    return PALETTE[index % len(PALETTE)]


# --------------------------------------------------------------------------- #
# Widget factories  (keep every screen visually consistent)
# --------------------------------------------------------------------------- #
def make_button(parent, text, command, bg=None, fg="#ffffff", width=None):
    """A flat themed button with a subtle hover effect."""
    bg = bg or Theme.ACCENT
    btn = tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=fg, activebackground=Theme.PANEL_LIGHT,
        activeforeground=fg, relief="flat", bd=0,
        font=(Theme.FONT, 10, "bold"),
        padx=12, pady=6, cursor="hand2",
    )
    if width:
        btn.config(width=width)
    btn.bind("<Enter>", lambda _e: btn.config(bg=_lighten(bg)))
    btn.bind("<Leave>", lambda _e: btn.config(bg=bg))
    return btn


def make_label(parent, text, size=11, bold=False, fg=None, bg=None):
    return tk.Label(
        parent, text=text,
        font=(Theme.FONT, size, "bold" if bold else "normal"),
        fg=fg or Theme.TEXT, bg=bg or Theme.PANEL,
    )


def make_entry(parent, width=20, show=None):
    return tk.Entry(
        parent, width=width, show=show,
        bg=Theme.PANEL_LIGHT, fg=Theme.TEXT,
        insertbackground=Theme.TEXT, relief="flat",
        font=(Theme.FONT, 11),
    )


def center_window(win, width, height):
    """Centre a Tk window/Toplevel on the screen."""
    win.update_idletasks()
    sw = win.winfo_screenwidth()
    sh = win.winfo_screenheight()
    x = (sw - width) // 2
    y = (sh - height) // 2
    win.geometry(f"{width}x{height}+{x}+{y}")


def _lighten(hex_color, amount=20):
    """Lighten a #rrggbb colour by a small amount for hover states."""
    hex_color = hex_color.lstrip("#")
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (0, 2, 4))
    return f"#{min(255, r + amount):02x}{min(255, g + amount):02x}{min(255, b + amount):02x}"


# --------------------------------------------------------------------------- #
# Data helpers
# --------------------------------------------------------------------------- #
def read_json(path, default=None):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return default if default is not None else []


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_settings():
    return read_json(SETTINGS_FILE, default={}) or {}


def save_settings(updates):
    settings = load_settings()
    settings.update(updates)
    write_json(SETTINGS_FILE, settings)


def ensure_data_files():
    """Create the data/ directory and seed files if they are missing."""
    os.makedirs(DATA_DIR, exist_ok=True)

    if not os.path.exists(PROCESSES_FILE):
        write_json(PROCESSES_FILE, [
            {"pid": "P1", "arrival": 0, "burst": 5, "priority": 2},
            {"pid": "P2", "arrival": 1, "burst": 3, "priority": 1},
            {"pid": "P3", "arrival": 2, "burst": 8, "priority": 4},
            {"pid": "P4", "arrival": 3, "burst": 6, "priority": 3},
        ])

    if not os.path.exists(USERS_FILE):
        write_json(USERS_FILE, [
            {"username": "admin", "password": "admin", "role": "admin"},
            {"username": "user", "password": "user", "role": "standard"},
        ])

    if not os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "w", encoding="utf-8") as f:
            f.write("Welcome to MiniOS Notepad!\n")

    if not os.path.exists(DISK_FILE):
        write_json(DISK_FILE, {
            "type": "folder", "name": "root", "children": [
                {"type": "folder", "name": "documents", "children": [
                    {"type": "file", "name": "readme.txt",
                     "content": "This is a virtual file inside MiniOS."}]},
                {"type": "folder", "name": "system", "children": []},
            ]})

    if not os.path.exists(LOGS_FILE):
        with open(LOGS_FILE, "w", encoding="utf-8") as f:
            f.write("")
