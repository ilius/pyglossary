#!/usr/bin/python3

import sys
from os.path import join, dirname, abspath
import unittest
import logging

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.entry import *
from pyglossary.core_test import getMockLogger

class TestEntrySqliteSortKeyFrom(unittest.TestCase):
	def sortKey1(self, words: "List[str]"):
		return words[0]

	def sortKey2(self, words: "List[str]"):
		return [words[0].lower(), words[0]]

	def sortKey3(self, words: "List[str]"):
		return [len(words[0])] + words

	def test_1(self):
		sqliteSortKey = Entry.sqliteSortKeyFrom(self.sortKey1)
		self.assertEqual(len(sqliteSortKey), 1)
		self.assertEqual(sqliteSortKey[0][0], "sortkey")
		self.assertEqual(sqliteSortKey[0][1], "TEXT")
		self.assertEqual(sqliteSortKey[0][2](["a", "b"]), "a")

	def test_2(self):
		sqliteSortKey = Entry.sqliteSortKeyFrom(self.sortKey2)
		self.assertEqual(len(sqliteSortKey), 2)
		self.assertEqual(sqliteSortKey[0][0], "sortkey_p1")
		self.assertEqual(sqliteSortKey[1][0], "sortkey_p2")
		self.assertEqual(sqliteSortKey[0][1], "TEXT")
		self.assertEqual(sqliteSortKey[1][1], "TEXT")
		self.assertEqual(sqliteSortKey[0][2](["a", "b"]), "a")
		self.assertEqual(sqliteSortKey[0][2](["AbC", "b"]), "abc")
		self.assertEqual(sqliteSortKey[1][2](["a", "b"]), "a")
		self.assertEqual(sqliteSortKey[1][2](["AbC", "b"]), "AbC")

	def test_3(self):
		sqliteSortKey = Entry.sqliteSortKeyFrom(self.sortKey3)
		self.assertEqual(len(sqliteSortKey), 3)
		self.assertEqual(sqliteSortKey[0][0], "sortkey_p1")
		self.assertEqual(sqliteSortKey[1][0], "sortkey_p2")
		self.assertEqual(sqliteSortKey[2][0], "sortkey_p3")
		self.assertEqual(sqliteSortKey[0][1], "INTEGER")
		self.assertEqual(sqliteSortKey[1][1], "TEXT")
		self.assertEqual(sqliteSortKey[2][1], "TEXT")
		self.assertEqual(sqliteSortKey[0][2](["a", "b"]), 1)
		self.assertEqual(sqliteSortKey[1][2](["a", "b", "c"]), "a")
		self.assertEqual(sqliteSortKey[2][2](["a", "b", "c"]), "b")


class TestEntryStripFullHtml(unittest.TestCase):
	def __init__(self, *args, **kwargs):
		unittest.TestCase.__init__(self, *args, **kwargs)
		self.mockLog = getMockLogger()

	def setUp(self):
		self.mockLog.clear()

	def tearDown(self):
		self.assertEqual(0, self.mockLog.printRemainingErrors())

	def case(
		self,
		word: str,
		origDefi: str,
		fixedDefi: str,
		logMsg: str = "",
		logLevel: int = logging.ERROR,
	):
		entry = Entry(word, origDefi)
		entry.stripFullHtml()
		self.assertEqual(entry.defi, fixedDefi)
		if logMsg:
			record = self.mockLog.popLog(logLevel, logMsg)
			self.assertIsNotNone(record, msg=f"logMsg={logMsg!r}")

	def test_1(self):
		self.case(
			word="test1",
			origDefi="plain text",
			fixedDefi="plain text",
			logMsg="",
		)

	def test_2(self):
		self.case(
			word="test2",
			origDefi="<p>simple <i>html</i> text</p>",
			fixedDefi="<p>simple <i>html</i> text</p>",
			logMsg="",
		)

	def test_3(self):
		self.case(
			word="test3",
			origDefi="<!DOCTYPE html><html><head></head><body>simple <i>html</i></body></html>",
			fixedDefi="simple <i>html</i>",
			logMsg="",
		)

	def test_4(self):
		self.case(
			word="test4",
			origDefi="<html><head></head><body>simple <i>html</i></body></html>",
			fixedDefi="simple <i>html</i>",
			logMsg="",
		)

	def test_5(self):
		self.case(
			word="test5",
			origDefi="<!DOCTYPE html><html><head></head>simple <i>html</i></html>",
			fixedDefi="<!DOCTYPE html><html><head></head>simple <i>html</i></html>",
			logMsg="<body not found: word=test5",
			logLevel=logging.WARNING,
		)

	def test_6(self):
		self.case(
			word="test6",
			origDefi="<html><head></head>no <body",
			fixedDefi="<html><head></head>no <body",
			logMsg="'>' after <body not found: word=test6",
		)

	def test_7(self):
		self.case(
			word="test7",
			origDefi="<html><head></head><body>",
			fixedDefi="<html><head></head><body>",
			logMsg="</body close not found: word=test7",
		)


if __name__ == "__main__":
	unittest.main()
