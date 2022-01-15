#!/usr/bin/python3

import sys
import os
from os.path import join, dirname, abspath, isdir, isfile
import unittest
import logging

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from tests.glossary_test import TestGlossaryBase, appTmpDir
from pyglossary.glossary import Glossary
from pyglossary.core_test import getMockLogger
from pyglossary.os_utils import rmtree


Glossary.init()


class TestGlossaryErrors(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)
		self.mockLog = getMockLogger()

	def setUp(self):
		TestGlossaryBase.setUp(self)
		self.mockLog.clear()

	def tearDown(self):
		TestGlossaryBase.tearDown(self)
		self.assertEqual(0, self.mockLog.printRemainingErrors())

	def assertLogCritical(self, errorMsg):
		self.assertIsNotNone(self.mockLog.popLog(
			logging.CRITICAL,
			errorMsg,
		), msg=f"did not find critical log {errorMsg!r}")

	def assertLogError(self, errorMsg):
		self.assertIsNotNone(self.mockLog.popLog(
			logging.ERROR,
			errorMsg,
		), msg=f"did not find error log {errorMsg!r}")

	def assertLogWarning(self, errorMsg):
		self.assertIsNotNone(self.mockLog.popLog(
			logging.WARNING,
			errorMsg,
		), msg=f"did not find warning log {errorMsg!r}")

	def test_loadPlugins_invalidDir(self):
		Glossary.loadPlugins("/abc/def/ghe")
		self.assertLogCritical("Invalid plugin directory: '/abc/def/ghe'")

	def test_loadPlugin_moduleNotFound(self):
		Glossary.loadPlugin("abc.def.ghe")
		self.assertLogWarning("Module 'abc.def' not found, skipping plugin 'abc.def.ghe'")

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

	def test_detectInputFormat_err4(self):
		res = Glossary.detectInputFormat(
			filename="test",
			format="FooBar",
		)
		self.assertIsNone(res)
		self.assertLogCritical("Invalid format 'FooBar'")

	def test_detectInputFormat_ok1(self):
		res = Glossary.detectInputFormat(
			filename="test.txt.gz",
			format="",
		)
		self.assertEqual(res, ("test.txt.gz", "Tabfile", ""))

	def test_detectInputFormat_ok2(self):
		res = Glossary.detectInputFormat(
			filename="test.txt.zip",
			format="",
		)
		self.assertEqual(res, ("test.txt", "Tabfile", "zip"))

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

	def test_detectOutputFormat_err4_1(self):
		res = Glossary.detectOutputFormat(
			filename="",
			format="BabylonBgl",
			inputFilename="test.txt"
		)
		self.assertIsNone(res)
		self.assertLogCritical("plugin BabylonBgl does not support writing")

	def test_detectOutputFormat_err4_2(self):
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
		self.assertEqual(res, ("test", "Tabfile", ""))
		self.assertLogError("inputFilename is empty")

	def test_init_infoBadType(self):
		try:
			Glossary(info=["a"])
		except Exception as e:
			self.assertEqual(str(type(e)), "<class 'TypeError'>")
			self.assertEqual(
				str(e),
				"Glossary: `info` has invalid type, dict or OrderedDict expected",
			)
		else:
			self.fail("did not raise an exception")

	def test_cleanup_removed(self):
		glos = Glossary()
		tmpFname = "test_cleanup_removed"
		entry = glos.newDataEntry(tmpFname, b"test")

		tmpFpath = entry._tmpPath
		self.assertTrue(bool(tmpFpath), msg="entry tmpPath is empty")
		self.assertTrue(isfile(tmpFpath), msg=f"tmp file does not exist: {tmpFpath}")

		rmtree(appTmpDir)
		glos.cleanup()
		self.assertLogError(f"no such file or directory: {appTmpDir}")

	def test_convert_sameFilename(self):
		glos = Glossary()
		res = glos.convert(
			inputFilename="test.txt",
			outputFilename="test.txt",
		)
		self.assertIsNone(res)
		self.assertLogCritical("Input and output files are the same")

	def test_convert_dirExists(self):
		glos = Glossary()
		res = glos.convert(
			inputFilename="test.txt",
			outputFilename=self.tempDir,
			outputFormat="Stardict",
		)
		self.assertIsNone(res)
		self.assertLogCritical(f"Directory already exists: {self.tempDir}")

	def test_convert_fileNotFound(self):
		glos = Glossary()
		res = glos.convert(
			inputFilename="/abc/def/test.txt",
			outputFilename="test2.txt",
		)
		self.assertIsNone(res)
		self.assertLogCritical("[Errno 2] No such file or directory: '/abc/def/test.txt'")
		self.assertLogCritical("Reading file '/abc/def/test.txt' failed.")

	def test_convert_unableDetectOutputFormat(self):
		glos = Glossary()
		res = glos.convert(
			inputFilename="test.txt",
			outputFilename="test",
			outputFormat="",
		)
		self.assertIsNone(res)
		self.assertLogCritical("Unable to detect output format!")
		self.assertLogCritical("Writing file 'test' failed.")


if __name__ == "__main__":
	unittest.main()
