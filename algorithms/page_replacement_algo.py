"""algorithms/page_replacement_algo.py - Pure page-replacement logic (no GUI).

Every function takes a reference string and a frame capacity:
    pages  : list[int]  the sequence of page references
    frames : int        the number of physical frames available
and returns a dict:
    {
        "faults":     int,    total page faults,
        "hits":       int,    total hits,
        "hit_ratio":  float,  hits / len(pages)  (0.0 if empty),
        "steps":      list of per-reference dicts:
            {"page": int, "frames": [...resident pages after this step...],
             "fault": bool}
    }

A *hit* occurs when the referenced page is already resident; otherwise it is a
fault. While frames are not full, faults simply fill an empty slot. The "frames"
list in each step is a snapshot copy of the resident pages *after* processing
that reference. Inputs are never mutated.

Keeping the logic free of Tkinter makes it unit-testable (see tests/).
"""


def _summary(pages, faults, hits, steps):
    """Bundle results into the standard return dict."""
    total = len(pages)
    ratio = hits / total if total else 0.0
    return {"faults": faults, "hits": hits, "hit_ratio": ratio, "steps": steps}


def fifo(pages, frames):
    """First-In-First-Out page replacement.

    The page that has been resident the longest is evicted on a fault when the
    frames are full.
    """
    resident = []          # acts as a FIFO queue of resident pages
    faults = hits = 0
    steps = []

    for page in pages:
        if page in resident:
            hits += 1
            fault = False
        else:
            faults += 1
            fault = True
            if len(resident) < frames:
                resident.append(page)
            else:
                resident.pop(0)        # evict oldest
                resident.append(page)
        steps.append({"page": page, "frames": list(resident), "fault": fault})

    return _summary(pages, faults, hits, steps)


def lru(pages, frames):
    """Least Recently Used page replacement.

    On a fault with full frames, the page whose last use is furthest in the past
    is evicted.
    """
    resident = []          # ordered: index 0 = least recently used
    faults = hits = 0
    steps = []

    for page in pages:
        if page in resident:
            hits += 1
            fault = False
            resident.remove(page)
            resident.append(page)      # mark as most recently used
        else:
            faults += 1
            fault = True
            if len(resident) >= frames:
                resident.pop(0)        # evict least recently used
            resident.append(page)
        steps.append({"page": page, "frames": list(resident), "fault": fault})

    return _summary(pages, faults, hits, steps)


def optimal(pages, frames):
    """Belady's optimal page replacement.

    On a fault with full frames, evict the resident page whose next use is
    furthest in the future (or never used again).
    """
    resident = []
    faults = hits = 0
    steps = []

    for index, page in enumerate(pages):
        if page in resident:
            hits += 1
            fault = False
        else:
            faults += 1
            fault = True
            if len(resident) < frames:
                resident.append(page)
            else:
                victim = _farthest_future(resident, pages, index + 1)
                resident[resident.index(victim)] = page
        steps.append({"page": page, "frames": list(resident), "fault": fault})

    return _summary(pages, faults, hits, steps)


def _farthest_future(resident, pages, start):
    """Return the resident page whose next reference is furthest ahead.

    A page never referenced again is considered furthest (infinite distance) and
    is chosen immediately.
    """
    victim = resident[0]
    victim_distance = -1
    for candidate in resident:
        try:
            distance = pages.index(candidate, start)
        except ValueError:
            return candidate            # never used again -> best victim
        if distance > victim_distance:
            victim_distance = distance
            victim = candidate
    return victim
