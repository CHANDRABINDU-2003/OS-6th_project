"""ui/ - The MiniOS glass presentation layer.

A self-contained UI toolkit (colours, fonts, glass panels, rings, graphs, cards,
sidebar, top bar, dock, dashboard, info panel) used by the desktop shell. It
contains *no* operating-system logic -- every widget only reads kernel state and
calls back into the desktop's launch(). OS behaviour lives in core/, apps/ and
algorithms/ and is never touched from here.
"""
