"""algorithms/memory_algorithms.py - Pure memory-management logic (no GUI).

Two classic textbook topics:

(A) Contiguous memory allocation strategies (First / Best / Worst Fit).
    Each takes (blocks, processes):
        blocks    : list[int] of free block sizes
        processes : list[int] of process sizes
    and returns `allocation`, a list where allocation[i] is the index of the
    block assigned to process i, or -1 if the process could not be placed.
    The caller's `blocks` list is never mutated (we work on a copy).

(B) Paging / virtual-memory address translation.

Keeping this free of Tkinter makes it unit-testable (see tests/).
"""


# --------------------------------------------------------------------------- #
# (A) Contiguous allocation
# --------------------------------------------------------------------------- #
def first_fit(blocks, processes):
    """Assign each process to the FIRST block large enough to hold it.

    The chosen block's remaining size is reduced so later processes see the
    leftover space. Returns a list of block indices (or -1 when unplaced).
    """
    remaining = list(blocks)          # copy: never mutate the caller's list
    allocation = [-1] * len(processes)
    for i, size in enumerate(processes):
        for j, free in enumerate(remaining):
            if free >= size:
                allocation[i] = j
                remaining[j] -= size
                break
    return allocation


def best_fit(blocks, processes):
    """Assign each process to the SMALLEST block large enough to hold it.

    Returns a list of block indices (or -1 when unplaced).
    """
    remaining = list(blocks)
    allocation = [-1] * len(processes)
    for i, size in enumerate(processes):
        best = -1
        for j, free in enumerate(remaining):
            if free >= size and (best == -1 or free < remaining[best]):
                best = j
        if best != -1:
            allocation[i] = best
            remaining[best] -= size
    return allocation


def worst_fit(blocks, processes):
    """Assign each process to the LARGEST block large enough to hold it.

    Returns a list of block indices (or -1 when unplaced).
    """
    remaining = list(blocks)
    allocation = [-1] * len(processes)
    for i, size in enumerate(processes):
        worst = -1
        for j, free in enumerate(remaining):
            if free >= size and (worst == -1 or free > remaining[worst]):
                worst = j
        if worst != -1:
            allocation[i] = worst
            remaining[worst] -= size
    return allocation


def fragmentation(blocks, processes, allocation):
    """Report internal and external fragmentation for an allocation result.

    Returns a dict:
        internal : leftover space inside blocks that received at least one
                   process (size committed but unused by those blocks).
        external : total free space in blocks that hold no process at all.

    Note: with the multi-process-per-block model the simple textbook notion of
    "internal" is approximated as the unused tail of every used block.
    """
    used = [0] * len(blocks)
    holds_process = [False] * len(blocks)
    for size, blk in zip(processes, allocation):
        if blk != -1:
            used[blk] += size
            holds_process[blk] = True

    internal = sum(blocks[j] - used[j] for j in range(len(blocks))
                   if holds_process[j])
    external = sum(blocks[j] for j in range(len(blocks))
                   if not holds_process[j])
    return {"internal": internal, "external": external}


# --------------------------------------------------------------------------- #
# (B) Paging / virtual-memory address translation
# --------------------------------------------------------------------------- #
def build_page_table(num_pages, frame_assignments):
    """Build a page->frame dict for the first `num_pages` pages.

    `frame_assignments` is an iterable of frame numbers; pages beyond the
    supplied frames (or with a None frame) are left out (i.e. not resident).
    """
    table = {}
    frames = list(frame_assignments)
    for page in range(num_pages):
        if page < len(frames) and frames[page] is not None:
            table[page] = frames[page]
    return table


def translate(logical_address, page_size, page_table):
    """Translate a logical address into a physical address.

    page   = logical_address // page_size
    offset = logical_address %  page_size
    If the page is not present in `page_table` a page fault is reported and
    frame / physical_address are None; otherwise:
        physical_address = frame * page_size + offset

    Returns a dict:
        {"page", "offset", "frame", "physical_address", "fault"}
    """
    if page_size <= 0:
        raise ValueError("page_size must be a positive integer.")

    page = logical_address // page_size
    offset = logical_address % page_size

    if page not in page_table:
        return {"page": page, "offset": offset, "frame": None,
                "physical_address": None, "fault": True}

    frame = page_table[page]
    physical = frame * page_size + offset
    return {"page": page, "offset": offset, "frame": frame,
            "physical_address": physical, "fault": False}
