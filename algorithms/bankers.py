"""algorithms/bankers.py - Banker's Algorithm (deadlock avoidance/detection).

Pure logic, no Tkinter, so it stays unit-testable (see tests/).

Conventions:
    allocation, maximum, request : P x R matrices of ints (P processes, R resources)
    available                    : list of ints, length R

The safety algorithm decides whether the system is in a safe state and, if so,
returns a safe execution order of the processes.
"""


def need_matrix(allocation, maximum):
    """Return the Need matrix (need = max - allocation, elementwise)."""
    return [
        [maximum[i][j] - allocation[i][j] for j in range(len(allocation[i]))]
        for i in range(len(allocation))
    ]


def _le(a, b):
    """True if every element of a <= the matching element of b (componentwise)."""
    return all(x <= y for x, y in zip(a, b))


def is_safe(allocation, maximum, available):
    """Run the safety algorithm.

    Returns (safe, sequence):
        safe     : bool - True if a safe ordering exists
        sequence : list[int] - the safe order of process indices
                   (empty list when the state is unsafe / a deadlock).
    """
    num_proc = len(allocation)
    need = need_matrix(allocation, maximum)
    work = list(available)
    finish = [False] * num_proc
    sequence = []

    # Repeatedly find a process that can finish with the current work vector.
    progressed = True
    while progressed:
        progressed = False
        for i in range(num_proc):
            if not finish[i] and _le(need[i], work):
                # Process i can run to completion and release its resources.
                work = [work[j] + allocation[i][j] for j in range(len(work))]
                finish[i] = True
                sequence.append(i)
                progressed = True

    safe = all(finish)
    return (safe, sequence) if safe else (False, [])


def build_rag(allocation, request, num_resources):
    """Build a Resource Allocation Graph description.

    Allocation edges run resource -> process; request edges run process -> resource.
    Returns a dict: {"processes": [...], "resources": [...], "edges": [(from, to)]}.
    """
    num_proc = len(allocation)
    processes = [f"P{i}" for i in range(num_proc)]
    resources = [f"R{j}" for j in range(num_resources)]
    edges = []

    for i in range(num_proc):
        for j in range(num_resources):
            # Allocation edge: resource holds units assigned to the process.
            if allocation[i][j] > 0:
                edges.append((resources[j], processes[i]))
            # Request edge: process is currently waiting on the resource.
            if request and request[i][j] > 0:
                edges.append((processes[i], resources[j]))

    return {"processes": processes, "resources": resources, "edges": edges}
