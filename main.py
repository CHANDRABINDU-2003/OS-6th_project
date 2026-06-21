"""main.py - Entry point for the MiniOS Simulator.

Flow:  boot animation -> login -> desktop  (logout returns to login).

Run with:  python main.py   (from the project root)
"""

import tkinter as tk

from utils import ensure_data_files, center_window, Theme, ThemeManager
from ui import fonts
from core.kernel import get_kernel
from core.boot import BootScreen
from core.login import LoginScreen
from core.desktop import Desktop


class MiniOS:
    def __init__(self):
        ensure_data_files()
        ThemeManager.load_saved()
        get_kernel()  # initialise the kernel (logs boot)

        self.root = tk.Tk()
        self.root.title("MiniOS X Pro")
        fonts.init()  # pick the nicest installed UI/mono font now root exists
        self.root.configure(bg=Theme.BG)
        center_window(self.root, 1240, 800)
        self.root.minsize(1080, 700)

        self.current_screen = None
        self._show_boot()

    def _clear(self):
        if self.current_screen is not None:
            self.current_screen.destroy()
            self.current_screen = None

    def _show_boot(self):
        self._clear()
        self.current_screen = BootScreen(self.root, on_complete=self._show_login)

    def _show_login(self):
        self._clear()
        self.current_screen = LoginScreen(self.root, on_success=self._show_desktop)

    def _show_desktop(self):
        self._clear()
        self.current_screen = Desktop(self.root, on_logout=self._show_login)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    MiniOS().run()
