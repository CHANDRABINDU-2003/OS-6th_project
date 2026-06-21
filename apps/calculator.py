"""apps/calculator.py - A simple calculator application."""

import tkinter as tk

from utils import Theme, center_window
from core.logger import log


class CalculatorApp(tk.Toplevel):
    def __init__(self, root):
        super().__init__(root)
        self.title("Calculator")
        self.configure(bg=Theme.BG)
        center_window(self, 280, 380)
        self.resizable(False, False)

        self.expr = ""
        self.display = tk.StringVar(value="0")

        screen = tk.Label(self, textvariable=self.display, anchor="e",
                          bg=Theme.PANEL, fg=Theme.TEXT,
                          font=(Theme.FONT_MONO, 22), padx=14, pady=18)
        screen.pack(fill="x", padx=8, pady=8)

        grid = tk.Frame(self, bg=Theme.BG)
        grid.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        buttons = [
            ("C", 0, 0, Theme.ACCENT_3), ("(", 0, 1, Theme.PANEL_LIGHT),
            (")", 0, 2, Theme.PANEL_LIGHT), ("/", 0, 3, Theme.ACCENT_4),
            ("7", 1, 0, Theme.PANEL), ("8", 1, 1, Theme.PANEL),
            ("9", 1, 2, Theme.PANEL), ("*", 1, 3, Theme.ACCENT_4),
            ("4", 2, 0, Theme.PANEL), ("5", 2, 1, Theme.PANEL),
            ("6", 2, 2, Theme.PANEL), ("-", 2, 3, Theme.ACCENT_4),
            ("1", 3, 0, Theme.PANEL), ("2", 3, 1, Theme.PANEL),
            ("3", 3, 2, Theme.PANEL), ("+", 3, 3, Theme.ACCENT_4),
            ("0", 4, 0, Theme.PANEL), (".", 4, 1, Theme.PANEL),
            ("⌫", 4, 2, Theme.PANEL_LIGHT), ("=", 4, 3, Theme.ACCENT_2),
        ]
        for i in range(4):
            grid.columnconfigure(i, weight=1)
        for i in range(5):
            grid.rowconfigure(i, weight=1)

        for text, r, c, color in buttons:
            b = tk.Button(grid, text=text, command=lambda t=text: self.press(t),
                          bg=color, fg=Theme.TEXT, relief="flat", bd=0,
                          font=(Theme.FONT, 14, "bold"), cursor="hand2")
            b.grid(row=r, column=c, sticky="nsew", padx=3, pady=3)

        log("Calculator opened")

    def press(self, key):
        if key == "C":
            self.expr = ""
        elif key == "⌫":
            self.expr = self.expr[:-1]
        elif key == "=":
            self._evaluate()
            return
        else:
            self.expr += key
        self.display.set(self.expr or "0")

    def _evaluate(self):
        try:
            # Restrict eval to arithmetic characters only.
            allowed = set("0123456789.+-*/() ")
            if not set(self.expr) <= allowed:
                raise ValueError
            result = eval(self.expr, {"__builtins__": {}}, {})
            self.expr = str(result)
            self.display.set(self.expr)
        except (ValueError, SyntaxError, ZeroDivisionError, NameError):
            self.display.set("Error")
            self.expr = ""
