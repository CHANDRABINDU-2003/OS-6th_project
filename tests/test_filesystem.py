"""tests/test_filesystem.py - Tests for the virtual file system data layer.

Exercises the JSON read/write helpers and the on-disk virtual file system
structure used by the Files app and the Shell (they share data/disk.json).

Run from the project root:  python -m unittest tests.test_filesystem
"""

import os
import sys
import json
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import utils


def find_child(folder, name):
    """Return the child node with the given name, or None."""
    for c in folder.get("children", []):
        if c["name"] == name:
            return c
    return None


class TestJsonHelpers(unittest.TestCase):
    def test_roundtrip(self):
        data = {"type": "folder", "name": "root", "children": []}
        with tempfile.NamedTemporaryFile(
                "w", suffix=".json", delete=False) as f:
            path = f.name
        try:
            utils.write_json(path, data)
            self.assertEqual(utils.read_json(path), data)
        finally:
            os.remove(path)

    def test_read_missing_returns_default(self):
        self.assertEqual(
            utils.read_json("/no/such/file.json", default={"x": 1}), {"x": 1})


class TestVirtualDisk(unittest.TestCase):
    def test_default_disk_structure(self):
        disk = utils.read_json(utils.DISK_FILE)
        self.assertEqual(disk["type"], "folder")
        self.assertEqual(disk["name"], "root")
        docs = find_child(disk, "documents")
        self.assertIsNotNone(docs)
        self.assertEqual(docs["type"], "folder")

    def test_create_and_traverse(self):
        # Simulate creating a folder + file as the Shell/Files apps would.
        disk = {"type": "folder", "name": "root", "children": []}
        disk["children"].append(
            {"type": "folder", "name": "projects", "children": []})
        projects = find_child(disk, "projects")
        projects["children"].append(
            {"type": "file", "name": "todo.txt", "content": "hello"})
        todo = find_child(projects, "todo.txt")
        self.assertEqual(todo["type"], "file")
        self.assertEqual(todo["content"], "hello")

        # Round-trips through JSON unchanged.
        self.assertEqual(json.loads(json.dumps(disk)), disk)


if __name__ == "__main__":
    unittest.main()
