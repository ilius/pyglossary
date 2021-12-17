#!/usr/bin/python3

import sys
from os.path import join, dirname, abspath
import unittest
import logging

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.entry import *
from pyglossary.core_test import MockLogHandler

log = logging.getLogger("pyglossary")

for handler in log.handlers:
	log.removeHandler(handler)

mockLog = MockLogHandler()
log.addHandler(mockLog)


class TestEntryStripFullHtml(unittest.TestCase):
	def case(
		self,
		origDefi: str,
		fixedDefi: str,
		logMsg: str = "",
		logLevel: int = logging.ERROR,
	):
		entry = Entry("test", origDefi)
		entry.stripFullHtml()
		self.assertEqual(entry.defi, fixedDefi)
		# to check error, we need to mock Logger
		if logMsg:
			record = mockLog.popLog(logLevel, logMsg)
			self.assertIsNotNone(record, msg=f"logMsg={logMsg!r}")
		self.assertEqual(0, mockLog.printRemainingErrors())
		mockLog.clear()

	def test(self):
		self.case(
			"plain text",
			"plain text",
			"",
		)
		self.case(
			"<p>simple <i>html</i> text</p>",
			"<p>simple <i>html</i> text</p>",
			"",
		)
		self.case(
			"<!DOCTYPE html><html><head></head><body>simple <i>html</i></body></html>",
			"simple <i>html</i>",
			"",
		)
		self.case(
			"<html><head></head><body>simple <i>html</i></body></html>",
			"simple <i>html</i>",
			"",
		)
		self.case(
			"<!DOCTYPE html><html><head></head>simple <i>html</i></html>",
			"<!DOCTYPE html><html><head></head>simple <i>html</i></html>",
			"<body not found: word=test",
			logLevel=logging.WARNING,
		)
		self.case(
			"<html><head></head>no <body",
			"<html><head></head>no <body",
			"'>' after <body not found: word=test",
		)
		self.case(
			"<html><head></head><body>",
			"<html><head></head><body>",
			"</body close not found: word=test",
		)


if __name__ == "__main__":
	unittest.main()
