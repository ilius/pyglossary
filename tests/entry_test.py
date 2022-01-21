#!/usr/bin/python3

import sys
from os.path import join, dirname, abspath
import unittest
import logging

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.entry import *
from pyglossary.core_test import getMockLogger


class TestEntryBasic(unittest.TestCase):
	def test_exc_1(self):
		try:
			Entry(b"word", "defi")
		except TypeError as e:
			self.assertEqual(str(e), "invalid word type <class 'bytes'>")
		else:
			self.fail("must raise TypeError")

	def test_exc_2(self):
		try:
			Entry(("word",), "defi")
		except TypeError as e:
			self.assertEqual(str(e), "invalid word type <class 'tuple'>")
		else:
			self.fail("must raise TypeError")

	def test_exc_3(self):
		try:
			Entry("word", b"defi")
		except TypeError as e:
			self.assertEqual(str(e), "invalid defi type <class 'bytes'>")
		else:
			self.fail("must raise TypeError")

	def test_exc_4(self):
		try:
			Entry("word", ("defi",))
		except TypeError as e:
			self.assertEqual(str(e), "invalid defi type <class 'tuple'>")
		else:
			self.fail("must raise TypeError")

	def test_exc_5(self):
		try:
			Entry("word", "defi", "b")
		except ValueError as e:
			self.assertEqual(str(e), "invalid defiFormat 'b'")
		else:
			self.fail("must raise ValueError")

	def test_1(self):
		entry = Entry("test1", "something")
		self.assertEqual(entry.l_word, ["test1"])
		self.assertEqual(entry.defi, "something")

	def test_2(self):
		entry = Entry(["test1"], "something")
		self.assertEqual(entry.l_word, ["test1"])
		self.assertEqual(entry.defi, "something")

	def test_3(self):
		entry = Entry("test1", ["something"])
		self.assertEqual(entry.l_word, ["test1"])
		self.assertEqual(entry.defi, "something")

	def test_repr_1(self):
		entry = Entry("test1", "something")
		self.assertEqual(
			repr(entry),
			"Entry('test1', 'something', defiFormat='m')",
		)

	def test_repr_1(self):
		entry = Entry("test1", "something", defiFormat="h")
		self.assertEqual(
			repr(entry),
			"Entry('test1', 'something', defiFormat='h')",
		)

	def test_defiFormat_1(self):
		entry = Entry("test1", "something")
		self.assertEqual(entry.defiFormat, "m")

	def test_defiFormat_2(self):
		entry = Entry("test1", "something", defiFormat="h")
		self.assertEqual(entry.defiFormat, "h")

	def test_defiFormat_3(self):
		entry = Entry("test1", "something", defiFormat="h")
		entry.defiFormat = "x"
		self.assertEqual(entry.defiFormat, "x")

	def test_addAlt_1(self):
		entry = Entry("test1", "something")
		self.assertEqual(entry.l_word, ["test1"])
		entry.addAlt("test 1")
		self.assertEqual(entry.l_word, ["test1", "test 1"])


class TestEntryDetectDefiFormat(unittest.TestCase):
	def test_1(self):
		entry = Entry("test1", "something")
		entry.detectDefiFormat()
		self.assertEqual(entry.defiFormat, "m")

	def test_2(self):
		entry = Entry("test1", "something", defiFormat="h")
		entry.detectDefiFormat()
		self.assertEqual(entry.defiFormat, "h")

	def test_3(self):
		entry = Entry("test1", "something", defiFormat="x")
		entry.detectDefiFormat()
		self.assertEqual(entry.defiFormat, "x")

	def test_4(self):
		entry = Entry("test1", "<b>something</b>")
		entry.detectDefiFormat()
		self.assertEqual(entry.defiFormat, "h")

	def test_5(self):
		entry = Entry("test1", "<k>title</k>something")
		entry.detectDefiFormat()
		self.assertEqual(entry.defiFormat, "x")


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
