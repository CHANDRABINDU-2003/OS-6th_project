"""core/pcb.py - Process Control Block + process states.

The PCB is the kernel's record for every process. Every state change goes
through PCB.set_state(), which logs the transition, so the Kernel Log, Task
Manager and System Monitor always reflect reality. This is the spine the
scheduler, memory manager and monitors all read from.
"""

import time

from core.logger import log


class ProcessState:
    NEW = "NEW"
    READY = "READY"
    RUNNING = "RUNNING"
    WAITING = "WAITING"
    TERMINATED = "TERMINATED"

    ALL = (NEW, READY, RUNNING, WAITING, TERMINATED)


# Approximate memory footprint (MB) for a GUI app window, so the monitors can
# show believable, state-derived memory instead of random numbers.
APP_FOOTPRINT_MB = 24


class PCB:
    """One process.

    `ptype` is one of:
      * "system" - the kernel/desktop themselves (cannot be killed)
      * "app"    - a GUI window the user opened from the desktop
      * "user"   - a simulated workload process (Kernel.create_process)
    """

    def __init__(self, pid, name, *, ptype="user", priority=0,
                 arrival=0, burst=0, mem=0):
        self.pid = pid
        self.name = name
        self.ptype = ptype
        self.priority = priority
        self.arrival = arrival
        self.burst = burst              # total CPU time required
        self.remaining = burst          # CPU time still to run
        self.mem = mem                  # memory requested/held (MB)

        self.state = ProcessState.NEW
        self.program_counter = 0
        self.registers = {}             # saved/restored on context switch
        self.mem_base = None            # filled in by the memory manager
        self.open_files = []
        self.cpu_time = 0               # CPU time consumed so far
        self.waiting_time = 0
        self.created = time.time()

    # ------------------------------------------------------------------ #
    def set_state(self, new_state):
        """Transition to a new state and log it. No-op if unchanged."""
        if new_state == self.state:
            return
        old, self.state = self.state, new_state
        log(f"PID {self.pid} ({self.name}): {old} -> {new_state}")

    # ---- Views used by the monitors ---------------------------------- #
    def cpu_share(self):
        """Instantaneous CPU% this process contributes.

        Only a RUNNING process burns real CPU; a workload process running on
        the CPU dominates it, while idle app/system windows sip a little.
        """
        if self.state == ProcessState.RUNNING:
            return 60.0 if self.ptype == "user" else 8.0
        if self.ptype in ("app", "system") and self.state != ProcessState.TERMINATED:
            return 1.5
        return 0.0

    def display_mem(self):
        """Memory held by this process (MB)."""
        if self.mem:
            return float(self.mem)
        if self.ptype in ("app", "system"):
            return float(APP_FOOTPRINT_MB)
        return 0.0

    def to_row(self):
        """Flat dict for table display / back-compat with older callers."""
        return {
            "pid": self.pid,
            "name": self.name,
            "state": self.state,
            "ptype": self.ptype,
            "cpu": self.cpu_share(),
            "mem": self.display_mem(),
            "priority": self.priority,
        }
