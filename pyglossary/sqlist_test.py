#!/usr/bin/python3

import sys
import os
from os.path import join, isfile, dirname, abspath
import unittest
from typing import Optional, Tuple, List, Any
import logging

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.core import tmpDir, user
from pyglossary.sqlist import *

stardictSortColumns = [
	(
		"wordlower",
		"TEXT",
		lambda x: x[0].lower(),
	),
	(
		"word",
		"TEXT",
		lambda x: x[0],
	),
	# FIXME: does SQLite sort compares based on text bytes or Unicode?
]


def stardictSortKey(item: List):
	b_word = item[0].encode("utf-8")
	return b_word.lower(), b_word


class TestSqList(unittest.TestCase):
	def __init__(self, *args):
		unittest.TestCase.__init__(self, *args)
		self.basePath = join(tmpDir, f"{user}-entry_test-")
		self._tmpFiles = set()
		if os.getenv("NO_CLEANUP") != "1":
			self.addCleanup(self.removeTmpFiles)

		self.mem_ls_1 = [
			("test1", "definition 1", "m"),
			("test2", "definition 1", "m"),
			("1", "one", "m"),
			("2", "two", "m"),
			("A", "AA", "m"),
			("b", "123", "m"),
			("C", "456", "m"),
		]
		self.mem_ls_2 = [
			("test1", 123, 1),
			("test2", 123, 2),
			("1", 1, 100),
			("2", 2, 10),
			("A", 0, 0),
			("b", 4, 4),
			("C", 3, 3),
		]


	def removeTmpFiles(self):
		for filename in self._tmpFiles:
			os.remove(filename)

	def newList(self, filename, sortColumns, items=None, create=True):
		if create and isfile(filename):
			os.remove(filename)
		self._tmpFiles.add(filename)
		ls = SqList(filename, sortColumns, create=create, persist=True)
		if items is not None:
			for x in items:
				ls.append(x)
		return ls

	def case(self, mem_ls):
		ls = self.newList(f"{self.basePath}1", stardictSortColumns, mem_ls)

		self.assertEqual(list(ls), mem_ls)

		mem_ls_sorted = list(sorted(mem_ls, key=stardictSortKey))
		mem_ls_sorted_rev = list(reversed(mem_ls_sorted))

		ls.sort()
		self.assertEqual(list(ls), mem_ls_sorted)

		ls = self.newList(f"{self.basePath}2", stardictSortColumns, mem_ls)
		self.assertEqual(list(ls), mem_ls)
		ls.sort(reverse=True)
		self.assertEqual(list(ls), mem_ls_sorted_rev)

	def test_1(self):
		self.case(self.mem_ls_1)

	def test_2(self):
		self.case(self.mem_ls_2)

	def test_read(self):
		mem_ls = self.mem_ls_1
		mem_ls_sorted = list(sorted(mem_ls, key=stardictSortKey))

		ls = self.newList(f"{self.basePath}3", stardictSortColumns, mem_ls)
		ls.sort()
		del ls
		ls2 = self.newList(f"{self.basePath}3", stardictSortColumns, create=False)
		self.assertEqual(list(ls2), mem_ls_sorted)

	def test_add(self):
		ls = self.newList(f"{self.basePath}3", stardictSortColumns, self.mem_ls_1)
		ls += self.mem_ls_2

		mem_ls = self.mem_ls_1 + self.mem_ls_2
		mem_ls_sorted = list(sorted(mem_ls, key=stardictSortKey))

		self.assertEqual(list(ls), mem_ls)
		ls.sort()
		self.assertEqual(list(ls), mem_ls_sorted)


if __name__ == "__main__":
	unittest.main()
