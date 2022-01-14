#!/usr/bin/python3

import sys
import os
from os.path import join, dirname, abspath, isdir, isfile
import unittest
import logging

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.glossary import Glossary
from pyglossary.core_test import MockLogHandler


Glossary.init()

log = logging.getLogger("pyglossary")

for handler in log.handlers:
	log.removeHandler(handler)

mockLog = MockLogHandler()
log.addHandler(mockLog)


class TestGlossaryErrors(unittest.TestCase):
	def tearDown(self):
		self.assertEqual(0, mockLog.printRemainingErrors())
		mockLog.clear()

	def assertLogError(self, errorMsg):
		self.assertIsNotNone(mockLog.popLog(
			logging.ERROR,
			errorMsg,
		), msg=f"did not find error log {errorMsg!r}")

	def assertLogCritical(self, errorMsg):
		self.assertIsNotNone(mockLog.popLog(
			logging.CRITICAL,
			errorMsg,
		), msg=f"did not find critical log {errorMsg!r}")

	def test_detectInputFormat_err1(self):
		res = Glossary.detectInputFormat(
			filename="",
			format="",
		)
		self.assertIsNone(res)
		self.assertLogCritical("Unable to detect input format!")

	def test_detectInputFormat_err2(self):
		res = Glossary.detectInputFormat(
			filename="test.abcd",
			format="",
		)
		self.assertIsNone(res)
		self.assertLogCritical("Unable to detect input format!")

	def test_detectInputFormat_err3(self):
		res = Glossary.detectInputFormat(
			filename="test.sql",
			format="",
		)
		self.assertIsNone(res)
		self.assertLogCritical("plugin Sql does not support reading")

	def test_detectInputFormat_err3(self):
		res = Glossary.detectInputFormat(
			filename="test",
			format="FooBar",
		)
		self.assertIsNone(res)
		self.assertLogCritical("Invalid format 'FooBar'")

	def test_detectOutputFormat_err1(self):
		res = Glossary.detectOutputFormat(
			filename="",
			format="",
			inputFilename=""
		)
		self.assertIsNone(res)
		self.assertLogCritical("Invalid filename ''")

	def test_detectOutputFormat_err2(self):
		res = Glossary.detectOutputFormat(
			filename="test",
			format="FooBar",
			inputFilename=""
		)
		self.assertIsNone(res)
		self.assertLogCritical("Invalid format FooBar")

	def test_detectOutputFormat_err3(self):
		res = Glossary.detectOutputFormat(
			filename="",
			format="",
			inputFilename="test"
		)
		self.assertIsNone(res)
		self.assertLogCritical("No filename nor format is given for output file")

	def test_detectOutputFormat_err4(self):
		res = Glossary.detectOutputFormat(
			filename="test.bgl",
			format="",
			inputFilename=""
		)
		self.assertIsNone(res)
		self.assertLogCritical("plugin BabylonBgl does not support writing")

	def test_detectOutputFormat_err5(self):
		res = Glossary.detectOutputFormat(
			filename="test",
			format="",
			inputFilename="",
		)
		self.assertIsNone(res)
		self.assertLogCritical("Unable to detect output format!")


	def test_detectOutputFormat_err6(self):
		res = Glossary.detectOutputFormat(
			filename="test",
			format="Tabfile",
			inputFilename="",
			addExt=True,
		)
		self.assertEqual(res, ('test', 'Tabfile', ''))
		self.assertLogError("inputFilename is empty")





if __name__ == "__main__":
	unittest.main()
