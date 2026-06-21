"""core/desktop.py - Main desktop shell (glass dashboard).

Composes the ui/ toolkit into a five-region layout -- top bar, left navigator,
centre dashboard (animated wallpaper + app cards + live activity graph), right
system-info panel, and a macOS-style dock. A once-per-second poll reads live
kernel state and feeds the rings, graph and stats.

OS logic is untouched: launching an app still instantiates the same Toplevel
class and registers it with the kernel exactly as before.
"""

import time
import tkinter as tk
from tkinter import messagebox

from utils import Theme, ThemeManager
from core.logger import log
from core.kernel import get_kernel

# OS-concept apps
from apps.scheduler import SchedulerApp
from apps.memory import MemoryApp
from apps.filesystem import FileSystemApp
from apps.shell import ShellApp
from apps.taskmanager import TaskManagerApp
from apps.deadlock import DeadlockApp
from apps.disk_scheduler import DiskSchedulerApp
from apps.page_replacement import PageReplacementApp
from apps.process_state import ProcessStateApp
from apps.ipc import IPCApp
# Utility apps
from apps.calculator import CalculatorApp
from apps.notepad import NotepadApp
from apps.clock import ClockApp
# System apps
from apps.system_monitor import SystemMonitorApp
from apps.kernel_log import KernelLogApp
from apps.theme_manager import ThemeManagerApp

from ui import colors as C
from ui.topbar import TopBar
from ui.sidebar import Sidebar
from ui.dock import Dock
from ui.dashboard import Dashboard
from ui.statusbar import InfoPanel


# name, glyph, subtitle, accent-key, class, category
APP_CATALOG = [
    ("Scheduler",  "🧠", "FCFS · SJF · Priority · Round Robin", "accent", SchedulerApp,       "OS Concepts"),
    ("Memory",     "💾", "First / Best / Worst Fit · Paging",   "blue",   MemoryApp,          "OS Concepts"),
    ("Deadlock",   "🔗", "Banker's Algorithm · RAG",            "amber",  DeadlockApp,        "OS Concepts"),
    ("Disk Sched", "📀", "FCFS · SSTF · SCAN · C-SCAN · LOOK",  "green",  DiskSchedulerApp,   "OS Concepts"),
    ("Page Repl",  "📄", "FIFO · LRU · Optimal",                "accent", PageReplacementApp, "OS Concepts"),
    ("Proc State", "🔁", "New → Ready → Run → Wait → Exit",     "blue",   ProcessStateApp,    "OS Concepts"),
    ("IPC",        "📨", "Shared Memory · Queues · Pipes",      "green",  IPCApp,             "OS Concepts"),
    ("Files",      "📁", "Virtual hierarchical file system",    "amber",  FileSystemApp,      "System"),
    ("Shell",      "💻", "Unix-like terminal",                  "accent", ShellApp,           "System"),
    ("Task Mgr",   "📊", "Live processes & resources",          "blue",   TaskManagerApp,     "System"),
    ("Monitor",    "📈", "Real-time CPU / Memory / Disk",       "green",  SystemMonitorApp,   "System"),
    ("Kernel Log", "📜", "Live kernel event feed",              "accent", KernelLogApp,       "System"),
    ("Themes",     "🎨", "Switch the look & feel",              "amber",  ThemeManagerApp,    "System"),
    ("Calculator", "🧮", "Quick calculations",                  "blue",   CalculatorApp,      "Utilities"),
    ("Notepad",    "📝", "Scratch notes",                       "green",  NotepadApp,         "Utilities"),
    ("Clock",      "🕑", "Time & date",                         "accent", ClockApp,           "Utilities"),
]

# Show every catalogued app in the sidebar and dock.
SIDEBAR = [row[0] for row in APP_CATALOG]
DOCK = SIDEBAR.copy()

# Per-process thread estimate, so the System panel shows believable numbers.
_THREADS = {"system": 4, "app": 3, "user": 2}
_DISK_CAPACITY_GB = 8.0


class Desktop(tk.Frame):
    def __init__(self, root, on_logout=None):
        super().__init__(root, bg=C.bg())
        self.root = root
        self.on_logout = on_logout
        self.kernel = get_kernel()
        self.pack(fill="both", expand=True)

        self._cls = {row[0]: row[4] for row in APP_CATALOG}
        self._glyph = {row[0]: row[1] for row in APP_CATALOG}
        self.open_windows = {}
        self._alive = True
        self._boot_time = time.time()

        self._build()
        ThemeManager.subscribe(self._on_theme_change)
        self._poll()
        log("Desktop ready")

    # ------------------------------------------------------------------ #
    def _build(self):
        user = self.kernel.current_user
        uname = user["username"] if user else "guest"

        self.topbar = TopBar(self, on_logout=self.logout,
                             on_shutdown=self.shutdown)
        self.topbar.pack(side="top", fill="x")

        self.dock = Dock(self, [(n, self._glyph[n]) for n in DOCK],
                         self.launch, is_open=self._is_open)
        self.dock.pack(side="bottom", fill="x")

        middle = tk.Frame(self, bg=C.bg())
        middle.pack(fill="both", expand=True)

        self.sidebar = Sidebar(middle, [(n, self._glyph[n]) for n in SIDEBAR],
                               self.launch)
        self.sidebar.pack(side="left", fill="y")

        self.info = InfoPanel(middle)
        self.info.pack(side="right", fill="y")

        accents = {"accent": C.accent(), "blue": C.blue(),
                   "green": C.green(), "amber": C.amber()}
        cards = [(n, g, sub, accents[a])
                 for (n, g, sub, a, _cls, _cat) in APP_CATALOG]
        self.dashboard = Dashboard(middle, cards, self.launch,
                                   greeting=f"Welcome back, {uname}")
        self.dashboard.pack(side="left", fill="both", expand=True)

    # ---- live stats poll ---------------------------------------------- #
    def _poll(self):
        if not self._alive or not self.winfo_exists():
            return
        k = self.kernel
        live = k.live_processes()
        cpu = k.cpu_usage()
        mem_pct = k.mem_usage()
        disk_pct = k.disk_usage()
        threads = sum(_THREADS.get(p.ptype, 1) for p in live)
        mem_mb = sum(p.display_mem() for p in live)
        queue = len(k.ready_queue)

        self.dashboard.push_metrics(cpu, mem_pct, min(100, queue * 12))
        self.info.update_stats(
            cpu=cpu, mem_pct=mem_pct, processes=len(live), threads=threads,
            mem_mb=mem_mb, disk_gb=disk_pct / 100 * _DISK_CAPACITY_GB,
            uptime=self._uptime())
        self.info.update_running(
            [p.name for p in live if p.ptype == "app"])
        self.dock.refresh_indicators()

        self.after(1000, self._poll)

    def _uptime(self):
        secs = int(time.time() - self._boot_time)
        return f"{secs // 3600:02d}:{secs % 3600 // 60:02d}:{secs % 60:02d}"

    def _is_open(self, name):
        win = self.open_windows.get(name)
        return bool(win and win.winfo_exists())

    # ---- launching apps (unchanged behaviour) ------------------------- #
    def launch(self, name):
        cls = self._cls.get(name)
        if cls is None:
            return
        existing = self.open_windows.get(name)
        if existing and existing.winfo_exists():
            existing.lift()
            existing.focus_force()
            return
        win = cls(self.root)
        self.open_windows[name] = win
        self.kernel.register_process(name)
        win.bind("<Destroy>", lambda e, n=name: self._on_app_close(e, n))

    def _on_app_close(self, event, name):
        if event.widget is self.open_windows.get(name):
            self.open_windows.pop(name, None)

    # ------------------------------------------------------------------ #
    def _on_theme_change(self):
        for child in self.winfo_children():
            child.destroy()
        self.configure(bg=C.bg())
        self._build()

    def logout(self):
        if messagebox.askyesno("Logout", "Log out of MiniOS?"):
            self._alive = False
            ThemeManager.unsubscribe(self._on_theme_change)
            self.kernel.logout()
            self.destroy()
            if self.on_logout:
                self.on_logout()

    def shutdown(self):
        if messagebox.askyesno("Shutdown", "Shut down MiniOS?"):
            self._alive = False
            log("System shutdown", level="BOOT")
            self.root.destroy()
