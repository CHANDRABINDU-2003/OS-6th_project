"""algorithms/cpu_scheduling.py - Pure CPU-scheduling logic (no GUI).

Every function takes a list of process dicts:
    {"pid": str, "arrival": int, "burst": int, "priority": int}
and returns (results, timeline):
    results  : list of dicts with added completion / turnaround / waiting
    timeline : list of (pid, start, end) Gantt segments

Keeping the logic free of Tkinter makes it unit-testable (see tests/).
"""


def _finalize(procs, completion):
    """Given completion time per pid, compute turnaround and waiting times."""
    by_pid = {p["pid"]: p for p in procs}
    results = []
    for pid, comp in completion.items():
        p = by_pid[pid]
        tat = comp - p["arrival"]
        wt = tat - p["burst"]
        results.append({**p, "completion": comp,
                        "turnaround": tat, "waiting": wt})
    results.sort(key=lambda r: r["pid"])
    return results


def fcfs(procs):
    order = sorted(procs, key=lambda p: (p["arrival"], p["pid"]))
    time, timeline, completion = 0, [], {}
    for p in order:
        start = max(time, p["arrival"])
        end = start + p["burst"]
        timeline.append((p["pid"], start, end))
        completion[p["pid"]] = end
        time = end
    return _finalize(procs, completion), timeline


def sjf(procs):
    """Shortest Job First (non-preemptive)."""
    remaining = list(procs)
    time, timeline, completion = 0, [], {}
    while remaining:
        ready = [p for p in remaining if p["arrival"] <= time]
        if not ready:
            time = min(p["arrival"] for p in remaining)
            continue
        p = min(ready, key=lambda x: (x["burst"], x["arrival"], x["pid"]))
        end = time + p["burst"]
        timeline.append((p["pid"], time, end))
        completion[p["pid"]] = end
        time = end
        remaining.remove(p)
    return _finalize(procs, completion), timeline


def priority_np(procs):
    """Priority scheduling (non-preemptive). Lower number = higher priority."""
    remaining = list(procs)
    time, timeline, completion = 0, [], {}
    while remaining:
        ready = [p for p in remaining if p["arrival"] <= time]
        if not ready:
            time = min(p["arrival"] for p in remaining)
            continue
        p = min(ready, key=lambda x: (x["priority"], x["arrival"], x["pid"]))
        end = time + p["burst"]
        timeline.append((p["pid"], time, end))
        completion[p["pid"]] = end
        time = end
        remaining.remove(p)
    return _finalize(procs, completion), timeline


def round_robin(procs, quantum):
    """Round Robin with the given time quantum (positive integer)."""
    if quantum <= 0:
        raise ValueError("Quantum must be a positive integer.")

    order = sorted(procs, key=lambda p: (p["arrival"], p["pid"]))
    remaining = {p["pid"]: p["burst"] for p in procs}
    time, timeline, completion = 0, [], {}
    queue, i = [], 0

    def enqueue_arrivals(upto):
        nonlocal i
        while i < len(order) and order[i]["arrival"] <= upto:
            queue.append(order[i]["pid"])
            i += 1

    enqueue_arrivals(time)
    if not queue and order:
        time = order[0]["arrival"]
        enqueue_arrivals(time)

    while queue:
        pid = queue.pop(0)
        run = min(quantum, remaining[pid])
        end = time + run
        timeline.append((pid, time, end))
        remaining[pid] -= run
        time = end
        enqueue_arrivals(time)          # newcomers queue ahead of re-queue
        if remaining[pid] > 0:
            queue.append(pid)
        else:
            completion[pid] = end
        if not queue and i < len(order):  # idle gap until next arrival
            time = order[i]["arrival"]
            enqueue_arrivals(time)

    return _finalize(procs, completion), timeline


def multilevel_queue(procs, quantum=2):
    """Multilevel Queue scheduling.

    Processes with priority <= 1 are treated as 'system/foreground' and served
    with Round Robin; the rest are 'background' and served FCFS, but only after
    every higher-queue process has finished (fixed-priority between queues).
    """
    high = [p for p in procs if p["priority"] <= 1]
    low = [p for p in procs if p["priority"] > 1]

    timeline, completion = [], {}
    time = 0

    # --- High queue: Round Robin -------------------------------------- #
    if high:
        # Shift the RR sub-schedule so it starts at the global clock.
        res_h, tl_h = round_robin(high, quantum)
        for pid, s, e in tl_h:
            timeline.append((pid, s, e))
        for r in res_h:
            completion[r["pid"]] = r["completion"]
        time = max((e for _, _, e in tl_h), default=0)

    # --- Low queue: FCFS, starting after the high queue --------------- #
    for p in sorted(low, key=lambda x: (x["arrival"], x["pid"])):
        start = max(time, p["arrival"])
        end = start + p["burst"]
        timeline.append((p["pid"], start, end))
        completion[p["pid"]] = end
        time = end

    return _finalize(procs, completion), timeline


def averages(results):
    """Return (avg_turnaround, avg_waiting) for a results list."""
    n = len(results)
    if n == 0:
        return 0.0, 0.0
    return (sum(r["turnaround"] for r in results) / n,
            sum(r["waiting"] for r in results) / n)
