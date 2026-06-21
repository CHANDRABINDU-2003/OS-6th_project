"""tests/test_kernel.py - Unit tests for the kernel PCB spine.

Verifies the process table, lifecycle transitions and the state-derived system
statistics that the Task Manager and System Monitor render.

Run from the project root:  python -m unittest tests.test_kernel
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.kernel import Kernel, TOTAL_RAM_MB
from core.pcb import ProcessState, APP_FOOTPRINT_MB


class TestKernelLifecycle(unittest.TestCase):
    def setUp(self):
        # A fresh kernel per test (don't use the shared get_kernel singleton).
        self.k = Kernel()

    def test_boot_creates_system_processes(self):
        names = [p.name for p in self.k.live_processes()]
        self.assertIn("kernel", names)
        self.assertIn("desktop", names)
        self.assertTrue(all(p.state == ProcessState.RUNNING
                            for p in self.k.running))

    def test_create_process_enters_ready_queue(self):
        p = self.k.create_process("P1", burst=5, priority=2, mem=200)
        self.assertEqual(p.state, ProcessState.READY)
        self.assertIn(p, self.k.ready_queue)

    def test_full_lifecycle_transitions(self):
        p = self.k.create_process("P1", burst=3)
        self.k.dispatch(p.pid)
        self.assertEqual(p.state, ProcessState.RUNNING)
        self.k.block(p.pid)
        self.assertEqual(p.state, ProcessState.WAITING)
        self.k.wakeup(p.pid)
        self.assertEqual(p.state, ProcessState.READY)
        self.k.preempt(p.pid)            # READY -> stays READY (no-op guard)
        self.assertEqual(p.state, ProcessState.READY)
        self.k.dispatch(p.pid)
        self.k.terminate(p.pid)
        self.assertIsNone(self.k.get(p.pid))   # PCB removed from the table

    def test_system_process_cannot_be_terminated(self):
        sys_pid = self.k.running[0].pid
        self.k.terminate(sys_pid)
        self.assertIsNotNone(self.k.get(sys_pid))

    def test_pids_are_unique(self):
        pids = {self.k.create_process(f"P{i}").pid for i in range(20)}
        pids |= {self.k.register_process(f"App{i}") for i in range(20)}
        self.assertEqual(len(pids), 40)

    def test_mem_usage_is_state_derived(self):
        before = self.k.mem_usage()
        self.k.create_process("Big", burst=1, mem=512)
        after = self.k.mem_usage()
        # 512MB of the simulated RAM should show up as a real jump.
        self.assertAlmostEqual(after - before, 512 / TOTAL_RAM_MB * 100, places=3)

    def test_app_process_reports_footprint(self):
        pid = self.k.register_process("Notepad")
        pcb = self.k.get(pid)
        self.assertEqual(pcb.display_mem(), float(APP_FOOTPRINT_MB))
        self.assertEqual(pcb.state, ProcessState.RUNNING)


if __name__ == "__main__":
    unittest.main()
