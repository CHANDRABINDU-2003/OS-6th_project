"""tests/test_scheduler.py - Unit tests for CPU scheduling algorithms.

Run from the project root:  python -m unittest tests.test_scheduler
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algorithms import cpu_scheduling as cpu

PROCS = [
    {"pid": "P1", "arrival": 0, "burst": 5, "priority": 2},
    {"pid": "P2", "arrival": 1, "burst": 3, "priority": 1},
    {"pid": "P3", "arrival": 2, "burst": 8, "priority": 4},
    {"pid": "P4", "arrival": 3, "burst": 6, "priority": 3},
]
TOTAL_BURST = sum(p["burst"] for p in PROCS)


def served_time(timeline):
    return sum(end - start for _, start, end in timeline)


class TestScheduling(unittest.TestCase):
    def _check_conservation(self, results, timeline):
        # Every unit of CPU burst must appear exactly once in the timeline.
        self.assertEqual(served_time(timeline), TOTAL_BURST)
        # Waiting time is never negative.
        for r in results:
            self.assertGreaterEqual(r["waiting"], 0)
            self.assertEqual(r["turnaround"], r["waiting"] + r["burst"])

    def test_fcfs(self):
        results, timeline = cpu.fcfs(PROCS)
        self._check_conservation(results, timeline)
        # FCFS serves in arrival order: P1,P2,P3,P4 -> completions 5,8,16,22
        comp = {r["pid"]: r["completion"] for r in results}
        self.assertEqual(comp, {"P1": 5, "P2": 8, "P3": 16, "P4": 22})

    def test_sjf(self):
        results, timeline = cpu.sjf(PROCS)
        self._check_conservation(results, timeline)

    def test_priority(self):
        results, timeline = cpu.priority_np(PROCS)
        self._check_conservation(results, timeline)

    def test_round_robin(self):
        results, timeline = cpu.round_robin(PROCS, quantum=2)
        self._check_conservation(results, timeline)

    def test_round_robin_bad_quantum(self):
        with self.assertRaises(ValueError):
            cpu.round_robin(PROCS, quantum=0)

    def test_multilevel_queue(self):
        results, timeline = cpu.multilevel_queue(PROCS, quantum=2)
        self._check_conservation(results, timeline)

    def test_averages(self):
        results, _ = cpu.fcfs(PROCS)
        avg_tat, avg_wt = cpu.averages(results)
        self.assertAlmostEqual(avg_tat, 11.25)
        self.assertAlmostEqual(avg_wt, 5.75)


if __name__ == "__main__":
    unittest.main()
