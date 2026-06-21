"""algorithms/disk_algo.py - Pure disk-scheduling logic (no GUI).

Every function takes a list of cylinder request ints and an initial ``head``
position and returns ``(sequence, total_seek)``:
    sequence   : list of cylinder positions visited, STARTING WITH ``head``
    total_seek : sum of absolute differences between consecutive positions

The caller's request list is never mutated (copies are sorted as needed).
Keeping the logic free of Tkinter makes it unit-testable (see tests/).
"""


def _total_seek(sequence):
    """Sum of absolute distances between consecutive positions in sequence."""
    return sum(abs(sequence[i] - sequence[i - 1])
               for i in range(1, len(sequence)))


def fcfs(requests, head):
    """First Come First Serve - serve requests in the order given."""
    sequence = [head] + list(requests)
    return sequence, _total_seek(sequence)


def sstf(requests, head):
    """Shortest Seek Time First - always serve the nearest pending request."""
    pending = list(requests)
    sequence = [head]
    current = head
    while pending:
        nearest = min(pending, key=lambda r: (abs(r - current), r))
        pending.remove(nearest)
        sequence.append(nearest)
        current = nearest
    return sequence, _total_seek(sequence)


def scan(requests, head, disk_size, direction="up"):
    """SCAN (elevator): move toward one end servicing requests, reach the
    physical end, then reverse and service the rest."""
    ordered = sorted(requests)
    lower = [r for r in ordered if r < head]
    upper = [r for r in ordered if r >= head]
    sequence = [head]

    if direction == "up":
        sequence.extend(upper)
        if not upper or upper[-1] != disk_size - 1:
            sequence.append(disk_size - 1)   # travel to the upper end
        sequence.extend(reversed(lower))
    else:  # "down"
        sequence.extend(reversed(lower))
        if not lower or lower[0] != 0:
            sequence.append(0)               # travel to the lower end
        sequence.extend(upper)

    return sequence, _total_seek(sequence)


def cscan(requests, head, disk_size, direction="up"):
    """C-SCAN (circular): service one direction to the end, jump to the
    opposite end, then continue in the same direction."""
    ordered = sorted(requests)
    lower = [r for r in ordered if r < head]
    upper = [r for r in ordered if r >= head]
    sequence = [head]

    if direction == "up":
        sequence.extend(upper)
        if not upper or upper[-1] != disk_size - 1:
            sequence.append(disk_size - 1)   # travel to the upper end
        sequence.append(0)                   # wrap to the lower end
        sequence.extend(lower)
    else:  # "down"
        sequence.extend(reversed(lower))
        if not lower or lower[0] != 0:
            sequence.append(0)               # travel to the lower end
        sequence.append(disk_size - 1)       # wrap to the upper end
        sequence.extend(reversed(upper))

    return sequence, _total_seek(sequence)


def look(requests, head, direction="up"):
    """LOOK: like SCAN but only travel as far as the last request in each
    direction (never to the physical disk end)."""
    ordered = sorted(requests)
    lower = [r for r in ordered if r < head]
    upper = [r for r in ordered if r >= head]
    sequence = [head]

    if direction == "up":
        sequence.extend(upper)
        sequence.extend(reversed(lower))
    else:  # "down"
        sequence.extend(reversed(lower))
        sequence.extend(upper)

    return sequence, _total_seek(sequence)
