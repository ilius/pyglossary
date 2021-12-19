#!/usr/bin/python3
import sys
from os.path import join, dirname, abspath
import unittest

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.text_utils import *

class TestTextUtils(unittest.TestCase):
	def test_unescapeNTB(self):
		self.assertEqual("a", unescapeNTB("a", bar=False))
		self.assertEqual("a\t", unescapeNTB("a\\t", bar=False))
		self.assertEqual("a\n", unescapeNTB("a\\n", bar=False))
		self.assertEqual("\ta", unescapeNTB("\\ta", bar=False))
		self.assertEqual("\na", unescapeNTB("\\na", bar=False))
		self.assertEqual("a\tb\n", unescapeNTB("a\\tb\\n", bar=False))
		self.assertEqual("a\\b", unescapeNTB("a\\\\b", bar=False))
		self.assertEqual("a\\\tb", unescapeNTB("a\\\\\\tb", bar=False))
		self.assertEqual("a|b\tc", unescapeNTB("a|b\\tc", bar=False))
		self.assertEqual("a\\|b\tc", unescapeNTB("a\\|b\\tc", bar=False))
		self.assertEqual("a\\|b\tc", unescapeNTB("a\\\\|b\\tc", bar=False))
		self.assertEqual("|", unescapeNTB("\\|", bar=True))
		self.assertEqual("a|b", unescapeNTB("a\\|b", bar=True))
		self.assertEqual("a|b\tc", unescapeNTB("a\\|b\\tc", bar=True))

	def test_escapeNTB(self):
		self.assertEqual(escapeNTB("a", bar=False), "a")
		self.assertEqual(escapeNTB("a\t", bar=False), "a\\t")
		self.assertEqual(escapeNTB("a\n", bar=False), "a\\n")
		self.assertEqual(escapeNTB("\ta", bar=False), "\\ta")
		self.assertEqual(escapeNTB("\na", bar=False), "\\na")
		self.assertEqual(escapeNTB("a\tb\n", bar=False), "a\\tb\\n")
		self.assertEqual(escapeNTB("a\\b", bar=False), "a\\\\b")
		self.assertEqual(escapeNTB("a\\\tb", bar=False), "a\\\\\\tb")
		self.assertEqual(escapeNTB("a|b\tc", bar=False), "a|b\\tc")
		self.assertEqual(escapeNTB("a\\|b\tc", bar=False), "a\\\\|b\\tc")
		self.assertEqual(escapeNTB("|", bar=True), "\\|")
		self.assertEqual(escapeNTB("a|b", bar=True), "a\\|b")
		self.assertEqual(escapeNTB("a|b\tc", bar=True), "a\\|b\\tc")

	def test_splitByBarUnescapeNTB(self):
		f = splitByBarUnescapeNTB
		self.assertEqual(f(""), [""])
		self.assertEqual(f("|"), ["", ""])
		self.assertEqual(f("a"), ["a"])
		self.assertEqual(f("a|"), ["a", ""])
		self.assertEqual(f("|a"), ["", "a"])
		self.assertEqual(f("a|b"), ["a", "b"])
		self.assertEqual(f("a\\|b|c"), ["a|b", "c"])
		self.assertEqual(f("a\\\\1|b|c"), ["a\\1", "b", "c"])
		# self.assertEqual(f("a\\\\|b|c"), ["a\\", "b", "c"])  # FIXME


if __name__ == "__main__":
	unittest.main()
