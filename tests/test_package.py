"""Metadata tests for the importable package."""

import re
import unittest
from pathlib import Path

import tally


class PackageMetadataTests(unittest.TestCase):
    def test_module_version_matches_pyproject(self):
        pyproject = (Path(__file__).resolve().parents[1] / "pyproject.toml").read_text(
            encoding="utf-8"
        )
        match = re.search(r'^version = "([^"]+)"$', pyproject, re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(tally.__version__, match.group(1))


if __name__ == "__main__":
    unittest.main()
