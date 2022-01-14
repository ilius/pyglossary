#!/usr/bin/python3

import sys
from os.path import join, dirname, abspath
import unittest
import logging

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.entry import *
from pyglossary.core_test import getMockLogger


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
