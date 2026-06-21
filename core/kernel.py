"""core/kernel.py - The MiniOS kernel: the single source of truth.

Holds the user database (authentication) and the live **process table** (a dict
of PID -> PCB). Every GUI app, and every simulated workload process, is a PCB
here. The scheduler, memory manager, Task Manager and System Monitor all read
and mutate this one table, so the whole simulator stays in sync -- this is what
makes MiniOS behave like one integrated OS instead of separate demos.

State transitions follow the classic process lifecycle:

    NEW -> READY -> RUNNING -> TERMINATED
                 ^         |
                 |         v
                 +----- WAITING   (blocked on I/O)

A single shared instance is returned by get_kernel().
"""

import itertools

from utils import read_json, USERS_FILE
from core.logger import log
from core.pcb import PCB, ProcessState

# Total simulated physical memory (MB). Memory usage is reported against this.
TOTAL_RAM_MB = 1024


class Kernel:
    def __init__(self):
        self.current_user = None
        self.users = read_json(USERS_FILE, default=[])
        self.process_table = {}            # pid -> PCB
        self._pids = itertools.count(1)
        self._boot_system_processes()
        log("Kernel initialized", level="BOOT")

    def _boot_system_processes(self):
        """The kernel and desktop always exist and always run."""
        for name in ("kernel", "desktop"):
            pcb = PCB(self._new_pid(), name, ptype="system")
            pcb.set_state(ProcessState.RUNNING)
            self.process_table[pcb.pid] = pcb

    def _new_pid(self):
        return next(self._pids)

    # ---- Authentication ------------------------------------------------ #
    def authenticate(self, username, password):
        for u in self.users:
            if u["username"] == username and u["password"] == password:
                self.current_user = u
                log(f"User '{username}' authenticated")
                return True
        log(f"Failed login for '{username}'", level="WARN")
        return False

    def logout(self):
        if self.current_user:
            log(f"User '{self.current_user['username']}' logged out")
        self.current_user = None

    # ---- Process table / queue views ----------------------------------- #
    def get(self, pid):
        return self.process_table.get(pid)

    def processes_in(self, *states):
        return [p for p in self.process_table.values() if p.state in states]

    def live_processes(self):
        """Every PCB that has not terminated."""
        return [p for p in self.process_table.values()
                if p.state != ProcessState.TERMINATED]

    @property
    def ready_queue(self):
        return self.processes_in(ProcessState.READY)

    @property
    def running(self):
        return self.processes_in(ProcessState.RUNNING)

    @property
    def waiting(self):
        return self.processes_in(ProcessState.WAITING)

    @property
    def processes(self):
        """Back-compat view: live processes as flat rows ({pid, name, ...})."""
        return [p.to_row() for p in self.live_processes()]

    # ---- App processes (GUI windows) ----------------------------------- #
    def register_process(self, name):
        """Register an opened GUI window as a running 'app' process."""
        pcb = PCB(self._new_pid(), name, ptype="app")
        pcb.set_state(ProcessState.RUNNING)
        self.process_table[pcb.pid] = pcb
        log(f"App started: {name} (pid {pcb.pid})")
        return pcb.pid

    # ---- User / workload processes ------------------------------------- #
    def create_process(self, name, burst=1, arrival=0, priority=0, mem=0):
        """Create a simulated workload process and admit it to the ready queue.

        This is the entry point the scheduler/memory phases build on: a real
        process the CPU scheduler can dispatch and the memory manager can back
        with RAM.
        """
        pcb = PCB(self._new_pid(), name, ptype="user", priority=priority,
                  arrival=arrival, burst=burst, mem=mem)
        self.process_table[pcb.pid] = pcb
        pcb.set_state(ProcessState.READY)
        log(f"Process created: {name} (pid {pcb.pid})")
        return pcb

    # ---- State transitions --------------------------------------------- #
    def dispatch(self, pid):
        """READY -> RUNNING (scheduler gives the CPU to this process)."""
        pcb = self.get(pid)
        if pcb and pcb.state == ProcessState.READY:
            pcb.set_state(ProcessState.RUNNING)
        return pcb

    def preempt(self, pid):
        """RUNNING -> READY (time slice expired / higher-priority arrived)."""
        pcb = self.get(pid)
        if pcb and pcb.state == ProcessState.RUNNING:
            pcb.set_state(ProcessState.READY)
        return pcb

    def block(self, pid):
        """RUNNING -> WAITING (process issued a blocking I/O request)."""
        pcb = self.get(pid)
        if pcb and pcb.state == ProcessState.RUNNING:
            pcb.set_state(ProcessState.WAITING)
        return pcb

    def wakeup(self, pid):
        """WAITING -> READY (I/O completed; ready to run again)."""
        pcb = self.get(pid)
        if pcb and pcb.state == ProcessState.WAITING:
            pcb.set_state(ProcessState.READY)
        return pcb

    def terminate(self, pid):
        """Move a process to TERMINATED, release its memory, remove its PCB."""
        pcb = self.get(pid)
        if not pcb:
            return None
        if pcb.ptype == "system":
            log(f"Refused to terminate system process {pcb.name}", level="WARN")
            return pcb
        pcb.set_state(ProcessState.TERMINATED)
        if pcb.mem_base is not None:
            log(f"Memory released for pid {pid}")
        del self.process_table[pid]
        log(f"Process terminated (pid {pid}); PCB removed")
        return pcb

    # kept for callers that used the old name
    def kill_process(self, pid):
        return self.terminate(pid)

    # ---- System statistics (derived from real state) ------------------- #
    def cpu_usage(self):
        """CPU% = sum of what running/idle processes actually consume."""
        return min(100.0, sum(p.cpu_share() for p in self.live_processes()))

    def mem_usage(self):
        """Memory% = held memory across all live processes / total RAM."""
        used = sum(p.display_mem() for p in self.live_processes())
        return min(100.0, used / TOTAL_RAM_MB * 100.0)

    def disk_usage(self):
        """Disk activity tracks processes currently blocked on I/O.

        Phase 4 (interrupts + disk scheduler) makes this a real measurement;
        for now it rises while processes sit in the WAITING set.
        """
        return min(100.0, 8.0 + len(self.waiting) * 15.0)


_KERNEL = None


def get_kernel():
    """Return the shared Kernel instance, creating it on first use."""
    global _KERNEL
    if _KERNEL is None:
        _KERNEL = Kernel()
    return _KERNEL
