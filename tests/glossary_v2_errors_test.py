import logging
import os
import sys
import unittest
from os.path import abspath, dirname, isfile, join, relpath

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from glossary_v2_test import TestGlossaryBase, appTmpDir

from pyglossary.core_test import getMockLogger
from pyglossary.glossary_v2 import ConvertArgs, Glossary
from pyglossary.os_utils import rmtree

Glossary.init()


class MyStr(str):
	pass


class TestGlossaryErrorsBase(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)
		self.mockLog = getMockLogger()

	def setUp(self):
		TestGlossaryBase.setUp(self)
		self.mockLog.clear()

	def tearDown(self):
		TestGlossaryBase.tearDown(self)
		method = self._testMethodName
		self.assertEqual(0, self.mockLog.printRemainingErrors(method))
		warnCount = self.mockLog.printRemainingwWarnings(method)
		if warnCount > 0:
			print(
				f"Got {warnCount} unhandled warnings "
				f"from {self.__class__.__name__}: {self._testMethodName}\n",
			)

	def assertLogCritical(self, errorMsg):
		self.assertIsNotNone(
			self.mockLog.popLog(
				logging.CRITICAL,
				errorMsg,
			),
			msg=f"did not find critical log {errorMsg!r}",
		)

	def assertLogError(self, errorMsg):
		self.assertIsNotNone(
			self.mockLog.popLog(
				logging.ERROR,
				errorMsg,
			),
			msg=f"did not find error log {errorMsg!r}",
		)

	def assertLogWarning(self, errorMsg):
		self.assertIsNotNone(
			self.mockLog.popLog(
				logging.WARNING,
				errorMsg,
			),
			msg=f"did not find warning log {errorMsg!r}",
		)


def osRoot():
	if os.sep == "\\":
		return "C:\\"
	return "/"


if os.sep == "\\":
	osNoSuchFileOrDir = "[WinError 3] The system cannot find the path specified:"
else:
	osNoSuchFileOrDir = "[Errno 2] No such file or directory:"


class TestGlossaryErrors(TestGlossaryErrorsBase):
	def test_loadPlugins_invalidDir(self):
		path = join(osRoot(), "abc", "def", "ghe")
		Glossary.loadPlugins(path)
		self.assertLogCritical(f"Invalid plugin directory: {path!r}")

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
			filename="test1.txt.gz",
			format="",
		)
		self.assertEqual(res, ("test1.txt.gz", "Tabfile", ""))

	def test_detectInputFormat_ok2(self):
		res = Glossary.detectInputFormat(
			filename="test2.txt.zip",
			format="",
		)
		self.assertEqual(res, ("test2.txt", "Tabfile", "zip"))

	def test_detectOutputFormat_err1(self):
		res = Glossary.detectOutputFormat(
			filename="",
			format="",
			inputFilename="",
		)
		self.assertIsNone(res)
		self.assertLogCritical("Invalid filename ''")

	def test_detectOutputFormat_err2(self):
		res = Glossary.detectOutputFormat(
			filename="test",
			format="FooBar",
			inputFilename="",
		)
		self.assertIsNone(res)
		self.assertLogCritical("Invalid format FooBar")

	def test_detectOutputFormat_err3(self):
		res = Glossary.detectOutputFormat(
			filename="",
			format="",
			inputFilename="test",
		)
		self.assertIsNone(res)
		self.assertLogCritical("No filename nor format is given for output file")

	def test_detectOutputFormat_err4_1(self):
		res = Glossary.detectOutputFormat(
			filename="",
			format="BabylonBgl",
			inputFilename="test3.txt",
		)
		self.assertIsNone(res)
		self.assertLogCritical("plugin BabylonBgl does not support writing")

	def test_detectOutputFormat_err4_2(self):
		res = Glossary.detectOutputFormat(
			filename="test.bgl",
			format="",
			inputFilename="",
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

	def test_lang_err_get_source(self):
		glos = Glossary()
		glos.setInfo("sourcelang", "test")
		self.assertEqual(glos.sourceLangName, "")
		self.assertLogError("unknown language 'test'")

	def test_lang_err_get_target(self):
		glos = Glossary()
		glos.setInfo("targetlang", "test")
		self.assertEqual(glos.targetLangName, "")
		self.assertLogError("unknown language 'test'")

	def test_lang_err_set_source(self):
		glos = Glossary()
		glos.sourceLangName = "foobar"
		self.assertLogError("unknown language 'foobar'")
		self.assertEqual(glos.sourceLangName, "")

	def test_lang_err_set_target(self):
		glos = Glossary()
		glos.targetLangName = "foobar"
		self.assertLogError("unknown language 'foobar'")
		self.assertEqual(glos.targetLangName, "")

	def test_lang_err_setObj_source(self):
		glos = Glossary()
		try:
			glos.sourceLang = "foobar"
		except TypeError as e:
			self.assertEqual(str(e), "invalid lang='foobar', must be a Lang object")
		else:
			self.fail("must raise a TypeError")

	def test_lang_err_setObj_target(self):
		glos = Glossary()
		try:
			glos.targetLang = "foobar"
		except TypeError as e:
			self.assertEqual(str(e), "invalid lang='foobar', must be a Lang object")
		else:
			self.fail("must raise a TypeError")

	def test_config_attr_set_twice(self):
		glos = Glossary()
		glos.config = {"lower": True}
		self.assertEqual(glos.getConfig("lower", False), True)
		glos.config = {"lower": False}
		self.assertLogError("glos.config is set more than once")
		self.assertEqual(glos.getConfig("lower", False), True)

	def test_iter_empty(self):
		glos = Glossary()
		self.assertEqual(list(glos), [])

	def test_convert_typeErr_1(self):
		glos = Glossary()
		try:
			glos.convert(
				ConvertArgs(
					inputFilename=MyStr(""),
				),
			)
		except TypeError as e:
			self.assertEqual(str(e), "inputFilename must be str")
		else:
			self.fail("must raise TypeError")

	def test_convert_typeErr_2(self):
		glos = Glossary()
		try:
			glos.convert(
				ConvertArgs(
					inputFilename="",
					outputFilename=MyStr(""),
				),
			)
		except TypeError as e:
			self.assertEqual(str(e), "outputFilename must be str")
		else:
			self.fail("must raise TypeError")

	def test_convert_typeErr_3(self):
		glos = Glossary()
		try:
			glos.convert(
				ConvertArgs(
					inputFilename="",
					outputFilename="",
					inputFormat=MyStr(""),
				),
			)
		except TypeError as e:
			self.assertEqual(str(e), "inputFormat must be str")
		else:
			self.fail("must raise TypeError")

	def test_convert_typeErr_4(self):
		glos = Glossary()
		try:
			glos.convert(
				ConvertArgs(
					inputFilename="",
					outputFilename="",
					inputFormat="",
					outputFormat=MyStr(""),
				),
			)
		except TypeError as e:
			self.assertEqual(str(e), "outputFormat must be str")
		else:
			self.fail("must raise TypeError")

	def test_write_typeErr_1(self):
		glos = Glossary()
		try:
			glos.write(
				filename=MyStr(""),
				format="",
			)
		except TypeError as e:
			self.assertEqual(str(e), "filename must be str")
		else:
			self.fail("must raise TypeError")

	def test_write_typeErr_2(self):
		glos = Glossary()
		try:
			glos.write(
				filename="",
				format=MyStr(""),
			)
		except TypeError as e:
			self.assertEqual(str(e), "format must be str")
		else:
			self.fail("must raise TypeError")

	def test_convert_sameFilename(self):
		glos = Glossary()
		res = glos.convert(
			ConvertArgs(
				inputFilename="test4.txt",
				outputFilename="test4.txt",
			),
		)
		self.assertIsNone(res)
		self.assertLogCritical("Input and output files are the same")

	def test_convert_dirExists(self):
		glos = Glossary()
		tempFilePath = self.newTempFilePath("test_convert_dirExists")
		with open(tempFilePath, mode="w") as _file:
			_file.write("")
		res = glos.convert(
			ConvertArgs(
				inputFilename="test5.txt",
				outputFilename=self.tempDir,
				outputFormat="Stardict",
			),
		)
		self.assertIsNone(res)
		self.assertLogCritical(
			f"Directory already exists and not empty: {relpath(self.tempDir)}",
		)

	def test_convert_fileNotFound(self):
		glos = Glossary()
		inputFilename = join(osRoot(), "abc", "def", "test6.txt")
		res = glos.convert(
			ConvertArgs(
				inputFilename=inputFilename,
				outputFilename="test2.txt",
			),
		)
		self.assertIsNone(res)
		self.assertLogCritical(
			f"[Errno 2] No such file or directory: {inputFilename!r}",
		)
		self.assertLogCritical(f"Reading file {relpath(inputFilename)!r} failed.")

	def test_convert_unableDetectOutputFormat(self):
		glos = Glossary()
		res = glos.convert(
			ConvertArgs(
				inputFilename="test7.txt",
				outputFilename="test",
				outputFormat="",
			),
		)
		self.assertIsNone(res)
		self.assertLogCritical("Unable to detect output format!")
		self.assertLogCritical(f"Writing file {relpath('test')!r} failed.")

	def test_convert_writeFileNotFound_txt(self):
		outputFilename = join(
			appTmpDir,
			"test",
			"7de8cf6f17bc4c9abb439e71adbec95d.txt",
		)
		glos = Glossary()
		res = glos.convert(
			ConvertArgs(
				inputFilename=self.downloadFile("100-en-fa.txt"),
				outputFilename=outputFilename,
			),
		)
		self.assertIsNone(res)
		self.assertLogCritical(
			f"[Errno 2] No such file or directory: {outputFilename!r}",
		)
		self.assertLogCritical(f"Writing file {relpath(outputFilename)!r} failed.")

	def test_convert_writeFileNotFound_hdir(self):
		outputFilename = join(osRoot(), "test", "40e20107f5b04087bfc0ec0d61510017.hdir")
		glos = Glossary()
		res = glos.convert(
			ConvertArgs(
				inputFilename=self.downloadFile("100-en-fa.txt"),
				outputFilename=outputFilename,
			),
		)
		self.assertIsNone(res)
		self.assertLogCritical(
			f"{osNoSuchFileOrDir} {outputFilename!r}",
		)
		self.assertLogCritical(f"Writing file {relpath(outputFilename)!r} failed.")

	def test_convert_invalidSortKeyName(self):
		glos = self.glos = Glossary()
		outputFilename = self.newTempFilePath("none.txt")
		res = glos.convert(
			ConvertArgs(
				inputFilename=self.downloadFile("100-en-fa.txt"),
				outputFilename=outputFilename,
				sort=True,
				sortKeyName="blah",
			),
		)
		self.assertIsNone(res)
		self.assertLogCritical("invalid sortKeyName = 'blah'")

	# def test_collectDefiFormat_direct(self):
	# 	from pyglossary.glossary import Glossary as GlossaryLegacy
	# 	fname = "100-en-fa.txt"
	# 	glos = self.glos = GlossaryLegacy()
	# 	glos.read(self.downloadFile(fname), direct=True)
	# 	res = glos.collectDefiFormat(10)
	# 	self.assertIsNone(res)
	# 	self.assertLogError("collectDefiFormat: not supported in direct mode")


if __name__ == "__main__":
	unittest.main()
