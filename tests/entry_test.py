import sys
import unittest
from os.path import abspath, dirname
from typing import Optional

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.entry import Entry


class TestEntryBasic(unittest.TestCase):
	def test_exc_1(self):
		try:
			Entry(b"word", "defi")
		except TypeError as e:
			self.assertEqual(str(e), "invalid word type <class 'bytes'>")
		else:
			self.fail("must raise TypeError")

	def test_exc_2(self):
		Entry(("word",), "defi")

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

	def test_repr_2(self):
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


class TestEntryStripFullHtml(unittest.TestCase):
	def __init__(self, *args, **kwargs):
		unittest.TestCase.__init__(self, *args, **kwargs)

	def setUp(self):
		pass

	def tearDown(self):
		pass

	def case(
		self,
		word: str,
		origDefi: str,
		fixedDefi: str,
		error: "Optional[str]" = None,
	):
		entry = Entry(word, origDefi)
		actualError = entry.stripFullHtml()
		self.assertEqual(entry.defi, fixedDefi)
		self.assertEqual(actualError, error)

	def test_1(self):
		self.case(
			word="test1",
			origDefi="plain text",
			fixedDefi="plain text",
			error=None,
		)

	def test_2(self):
		self.case(
			word="test2",
			origDefi="<p>simple <i>html</i> text</p>",
			fixedDefi="<p>simple <i>html</i> text</p>",
			error=None,
		)

	def test_3(self):
		self.case(
			word="test3",
			origDefi=(
				"<!DOCTYPE html><html><head></head><body>simple "
				"<i>html</i></body></html>"
			),
			fixedDefi="simple <i>html</i>",
			error=None,
		)

	def test_4(self):
		self.case(
			word="test4",
			origDefi="<html><head></head><body>simple <i>html</i></body></html>",
			fixedDefi="simple <i>html</i>",
			error=None,
		)

	def test_5(self):
		self.case(
			word="test5",
			origDefi="<!DOCTYPE html><html><head></head>simple <i>html</i></html>",
			fixedDefi="<!DOCTYPE html><html><head></head>simple <i>html</i></html>",
			error="<body not found",
		)

	def test_6(self):
		self.case(
			word="test6",
			origDefi="<html><head></head>no <body",
			fixedDefi="<html><head></head>no <body",
			error="'>' after <body not found",
		)

	def test_7(self):
		self.case(
			word="test7",
			origDefi="<html><head></head><body>",
			fixedDefi="<html><head></head><body>",
			error="</body close not found",
		)


if __name__ == "__main__":
	unittest.main()
