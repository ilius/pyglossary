"""
Internal unit tests for Babylon BGL helper routines.

Exercises low-level BGL parsing helpers such as ASCII detection. Run via the
standard library test runner during Babylon BGL plugin development.
"""

import unittest

from pyglossary.plugins.babylon_bgl.reader_debug import isASCII


class BglInternalTest(unittest.TestCase):
	"""Tests for Bgl Internal Test."""

	def test_isASCII(self):
		f = isASCII
		self.assertEqual(f(""), True)
		self.assertEqual(f("abc"), True)
		self.assertEqual(f("xyz"), True)
		self.assertEqual(f("ABC"), True)
		self.assertEqual(f("XYZ"), True)
		self.assertEqual(f("1234567890"), True)
		self.assertEqual(f("\n\r\t"), True)
		self.assertEqual(f("\x80"), False)
		self.assertEqual(f("abc\x80"), False)
		self.assertEqual(f("abc\xff"), False)
