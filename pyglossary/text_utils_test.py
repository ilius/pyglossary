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
		self.assertEqual("|", unescapeNTB("\\|", bar=True))
		self.assertEqual("a|b", unescapeNTB("a\\|b", bar=True))
		self.assertEqual("a|b\tc", unescapeNTB("a\\|b\\tc", bar=True))

if __name__ == "__main__":
	unittest.main()
