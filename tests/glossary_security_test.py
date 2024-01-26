import logging
import os
import sys
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from glossary_errors_test import TestGlossaryErrors
from glossary_v2_test import testCacheDir

from pyglossary.glossary import Glossary


class TestGlossarySecurity(TestGlossaryErrors):
	def __init__(self, *args, **kwargs):
		TestGlossaryErrors.__init__(self, *args, **kwargs)
		self.mockLog.setLevel(logging.INFO)

	def test_convert_1(self):
		glos = Glossary()
		res = glos.convert(
			inputFilename="os.system('abcd')",
			outputFilename="os.system('abcd -l')",
		)
		self.assertIsNone(res)
		self.assertLogCritical("Unable to detect output format!")
		self.assertLogCritical(
			"Writing file \"os.system('abcd -l')\" failed.",
		)

	def test_convert_2(self):
		glos = Glossary()
		res = glos.convert(
			inputFilename="os.system('abcd');test.txt",
			outputFilename="os.system('abcd -l')",
		)
		self.assertIsNone(res)
		self.assertLogCritical("Unable to detect output format!")
		self.assertLogCritical(
			"Writing file \"os.system('abcd -l')\" failed.",
		)

	def test_convert_3(self):
		glos = Glossary()
		res = glos.convert(
			inputFilename="os.system('abcd');test.txt",
			outputFilename="os.system('abcd -l');test.csv",
		)
		self.assertIsNone(res)
		errMsg = (
			f"[Errno 2] No such file or directory: "
			f"\"{testCacheDir}{os.sep}os.system('abcd');test.txt\""
		)
		errMsg = errMsg.replace("\\", "\\\\")
		self.assertLogCritical(errMsg)
		self.assertLogCritical(
			"Reading file \"os.system('abcd');test.txt\" failed.",
		)

	def test_convert_4(self):
		glos = Glossary()
		res = glos.convert(
			inputFilename="test.txt\nos.system('abcd')",
			outputFilename="test.csv\nos.system('abcd -l')",
		)
		self.assertIsNone(res)
		self.assertLogCritical("Unable to detect output format!")
		self.assertLogCritical(
			"Writing file \"test.csv\\nos.system('abcd -l')\" failed.",
		)


if __name__ == "__main__":
	unittest.main()
