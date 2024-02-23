import sys
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.text_utils_extra import (
	formatHMS,
	unescapeBarBytes,
)


class TestTextUtilsExtra(unittest.TestCase):
	def test_formatHMS(self):
		f = formatHMS
		self.assertEqual(f(0, 0, 0), "00")
		self.assertEqual(f(0, 0, 9), "09")
		self.assertEqual(f(0, 0, 10), "10")
		self.assertEqual(f(0, 0, 59), "59")
		self.assertEqual(f(0, 1, 0), "01:00")
		self.assertEqual(f(0, 1, 5), "01:05")
		self.assertEqual(f(0, 5, 7), "05:07")
		self.assertEqual(f(0, 59, 0), "59:00")
		self.assertEqual(f(0, 59, 59), "59:59")
		self.assertEqual(f(1, 0, 0), "01:00:00")
		self.assertEqual(f(123, 5, 7), "123:05:07")
		self.assertEqual(f(123, 59, 59), "123:59:59")


	def test_unescapeBarBytes(self):
		f = unescapeBarBytes
		self.assertEqual(b"", f(b""))
		self.assertEqual(b"|", f(b"\\|"))
		self.assertEqual(b"a|b", f(b"a\\|b"))
		self.assertEqual(b"a|b\tc", f(b"a\\|b\tc"))
		self.assertEqual(b"a|b\\t\\nc", f(b"a\\|b\\t\\nc"))
		self.assertEqual(b"\\", f(b"\\\\"))
		self.assertEqual(b"\\|", f(b"\\\\\\|"))
