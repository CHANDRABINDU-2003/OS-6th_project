"""core/login.py - Authentication screen (glass redesign).

A centred glass login card -- avatar, "Welcome Back", username/password fields
and a glowing login button -- floating over the animated wallpaper. Credentials
are still checked against the kernel's user database (data/users.json); no auth
logic changed.
"""

import tkinter as tk

from ui import colors as C
from ui import fonts as F
from ui.animations import Wallpaper, hover
from ui.widgets import GlassPanel
from core.kernel import get_kernel


class LoginScreen(tk.Frame):
    def __init__(self, root, on_success):
        super().__init__(root, bg=C.bg())
        self.root = root
        self.on_success = on_success
        self.kernel = get_kernel()
        self.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self, bg=C.bg(), highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        self.wallpaper = Wallpaper(self.canvas, node_count=16, star_count=26)

        card = GlassPanel(self.canvas, pad=0)
        body = card.body
        body.configure(padx=44, pady=34)

        # Avatar
        avatar = tk.Canvas(body, width=72, height=72, bg=C.card(),
                           highlightthickness=0)
        avatar.create_oval(4, 4, 68, 68, fill=C.mix(C.card(), C.accent(), 0.5),
                           outline=C.accent(), width=2)
        avatar.create_text(36, 38, text="👤", font=F.ui(28))
        avatar.pack(pady=(0, 10))

        tk.Label(body, text="MiniOS X Pro", font=F.ui(20, "bold"),
                 fg=C.text(), bg=C.card()).pack()
        tk.Label(body, text="Welcome back", font=F.body(), fg=C.muted(),
                 bg=C.card()).pack(pady=(2, 20))

        self.user = self._field(body, "Username")
        self.user.insert(0, "udita")
        self.pwd = self._field(body, "Password", show="•")

        self.error = tk.Label(body, text="", font=F.small(), fg=C.red(),
                              bg=C.card())
        self.error.pack(pady=(8, 0))

        self.btn = tk.Label(body, text="Sign In", font=F.ui(11, "bold"),
                            bg=C.accent(), fg="#ffffff", cursor="hand2")
        self.btn.pack(fill="x", pady=(14, 6), ipady=9)
        self.btn.bind("<Button-1>", lambda _e: self._attempt())
        hover(self.btn, lambda: self.btn.config(bg=C.lighten(C.accent(), 0.16)),
              lambda: self.btn.config(bg=C.accent()))

        tk.Label(body, text="default:  udita / 2102006", font=F.small(),
                 fg=C.muted(), bg=C.card()).pack(pady=(8, 0))

        self.canvas.bind("<Configure>", lambda e: self.canvas.coords(
            self._win, e.width / 2, e.height / 2))
        self._win = self.canvas.create_window(0, 0, window=card)

        self.pwd.bind("<Return>", lambda _e: self._attempt())
        self.user.bind("<Return>", lambda _e: self.pwd.focus_set())
        self.after(120, self.pwd.focus_set)

    def _field(self, parent, label, show=None):
        tk.Label(parent, text=label, font=F.small(), fg=C.muted(),
                 bg=C.card()).pack(anchor="w", pady=(8, 2))
        entry = tk.Entry(parent, width=26, show=show, relief="flat",
                         bg=C.mix(C.card(), "#ffffff", 0.06), fg=C.text(),
                         insertbackground=C.text(), font=F.body())
        entry.pack(ipady=6, fill="x")
        return entry

    def _attempt(self):
        if self.kernel.authenticate(self.user.get().strip(), self.pwd.get()):
            self.on_success()
        else:
            self.error.config(text="Invalid username or password")
            self.pwd.delete(0, "end")
