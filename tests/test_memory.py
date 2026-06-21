"""tests/test_memory.py - Unit tests for memory allocation + paging.

Run from the project root:  python -m unittest tests.test_memory
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algorithms import memory_algorithms as mem


class TestContiguousAllocation(unittest.TestCase):
    def setUp(self):
        self.blocks = [100, 500, 200, 300, 600]
        self.procs = [212, 417, 112, 426]

    def test_first_fit(self):
        # Classic textbook answer for first fit.
        self.assertEqual(mem.first_fit(self.blocks, self.procs), [1, 4, 1, -1])

    def test_best_fit(self):
        self.assertEqual(mem.best_fit(self.blocks, self.procs), [3, 1, 2, 4])

    def test_worst_fit(self):
        self.assertEqual(mem.worst_fit(self.blocks, self.procs), [4, 1, 4, -1])

    def test_inputs_not_mutated(self):
        original = list(self.blocks)
        mem.first_fit(self.blocks, self.procs)
        self.assertEqual(self.blocks, original)


class TestPaging(unittest.TestCase):
    def test_translate_hit(self):
        page_table = {0: 5, 1: 2, 2: 7}
        # logical addr 1 page in, offset 4, page size 10 -> page 1, frame 2
        res = mem.translate(14, 10, page_table)
        self.assertFalse(res["fault"])
        self.assertEqual(res["page"], 1)
        self.assertEqual(res["offset"], 4)
        self.assertEqual(res["frame"], 2)
        self.assertEqual(res["physical_address"], 24)

    def test_translate_fault(self):
        page_table = {0: 5}
        res = mem.translate(35, 10, page_table)  # page 3 not mapped
        self.assertTrue(res["fault"])
        self.assertIsNone(res["frame"])


if __name__ == "__main__":
    unittest.main()
