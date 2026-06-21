"""ui/animations.py - Hover effects and the animated wallpaper.

Tkinter can't scale or blur widgets, so "animation" here means colour/border
transitions, a small positional lift (dock), and a drifting particle field drawn
on a Canvas. Everything is cheap and driven by widget.after().
"""

import math
import random

from ui import colors as C


def hover(widget, enter, leave):
    """Bind enter/leave callbacks (and propagate from child labels)."""
    widget.bind("<Enter>", lambda _e: enter())
    widget.bind("<Leave>", lambda _e: leave())


class Wallpaper:
    """Sci-fi background: vertical gradient + glowing nodes + network lines +
    a few slowly drifting stars. Pure decoration drawn on a Canvas."""

    def __init__(self, canvas, node_count=14, star_count=22, animate=True):
        self.c = canvas
        self.node_count = node_count
        self.star_count = star_count
        self.animate = animate
        self.w = self.h = 0
        self.nodes = []     # (x, y) glowing graph nodes
        self.stars = []     # [x, y, r, speed]
        self._alive = True
        canvas.bind("<Configure>", self._on_configure)
        if animate:
            self._tick()

    # ------------------------------------------------------------------ #
    def _on_configure(self, event):
        if (event.width, event.height) == (self.w, self.h):
            return
        self.w, self.h = event.width, event.height
        self._seed()
        self._draw_static()

    def _seed(self):
        w, h = max(self.w, 1), max(self.h, 1)
        self.nodes = [(random.randint(0, w), random.randint(0, h))
                      for _ in range(self.node_count)]
        self.stars = [[random.randint(0, w), random.randint(0, h),
                       random.choice((1, 1, 2)), random.uniform(0.15, 0.6)]
                      for _ in range(self.star_count)]

    def _draw_static(self):
        c = self.c
        c.delete("wp")
        # Gradient: a hint of accent at the top fading into the base BG.
        top = C.mix(C.bg(), C.accent(), 0.12)
        steps = 64
        for i in range(steps):
            col = C.mix(top, C.bg(), i / steps)
            y0 = int(self.h * i / steps)
            y1 = int(self.h * (i + 1) / steps)
            c.create_rectangle(0, y0, self.w, y1, fill=col, width=0, tags="wp")
        # Network lines between nearby nodes.
        line_col = C.mix(C.bg(), C.accent(), 0.35)
        for i, (x1, y1) in enumerate(self.nodes):
            for x2, y2 in self.nodes[i + 1:]:
                if math.hypot(x2 - x1, y2 - y1) < min(self.w, self.h) * 0.28:
                    c.create_line(x1, y1, x2, y2, fill=line_col, tags="wp")
        # Glowing nodes (layered halo).
        for x, y in self.nodes:
            for r, t in ((9, 0.78), (5, 0.45), (2, 0.0)):
                c.create_oval(x - r, y - r, x + r, y + r, width=0,
                              fill=C.mix(C.bg(), C.accent(), 1 - t), tags="wp")
        c.tag_lower("wp")

    def _tick(self):
        if not self._alive:
            return
        try:
            self.c.delete("star")
            star_col = C.mix(C.bg(), C.text(), 0.85)
            for s in self.stars:
                s[1] -= s[3]
                if s[1] < 0:
                    s[0] = random.randint(0, max(self.w, 1))
                    s[1] = self.h
                r = s[2]
                self.c.create_oval(s[0] - r, s[1] - r, s[0] + r, s[1] + r,
                                   width=0, fill=star_col, tags="star")
            self.c.tag_raise("star", "wp")
            self.c.after(60, self._tick)
        except Exception:
            self._alive = False

    def stop(self):
        self._alive = False
