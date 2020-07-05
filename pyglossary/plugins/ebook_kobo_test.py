#!/usr/bin/env python3

from os.path import join, dirname, abspath
import sys
import unittest


rootDir = dirname(dirname(dirname(abspath(__file__))))
sys.path.insert(0, rootDir)

from pyglossary.plugins.ebook_kobo import (
	Writer,
)

class GetPrefixTest(unittest.TestCase):
	def case(self, word, prefix):
		w = Writer(None)
		self.assertEqual(
			w.get_prefix(word),
			prefix,
		)

	def test(self):
		# test cases are copied from
		# https://pgaskin.net/dictutil/dicthtml/prefixes.html
		self.case("test", "te")
		self.case("a", "aa")
		self.case("Èe", "èe")
		self.case("multiple words", "mu")
		self.case("àççèñts", "àç")
		self.case("à", "àa")
		self.case("ç", "ça")
		self.case("", "11")
		self.case(" ", "11")
		self.case(" x", "xa")
		self.case(" 123", "11")
		self.case("x 23", "xa")
		self.case("д ", "д")
		self.case("дaд", "дa")
		self.case("未未", "未未")
		self.case("未", "未a")
		self.case("  未", "11")
		self.case(" 未", "未a")

if __name__ == "__main__":
	unittest.main()
