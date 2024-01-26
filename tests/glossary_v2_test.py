import hashlib
import logging
import os
import random
import sys
import tempfile
import tracemalloc
import unittest
import zipfile
from os.path import abspath, dirname, isdir, isfile, join
from typing import Callable, Optional
from urllib.request import urlopen

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.core import cacheDir, log, tmpDir
from pyglossary.glossary_v2 import ConvertArgs, Glossary
from pyglossary.os_utils import rmtree
from pyglossary.text_utils import crc32hex

tracemalloc.start()

Glossary.init()

repo = os.getenv(
	"PYGLOSSARY_TEST_REPO",
	"ilius/pyglossary-test/main",
)

dataURL = f"https://raw.githubusercontent.com/{repo}/{{filename}}"

testCacheDir = join(cacheDir, "test")
appTmpDir = join(cacheDir, "tmp")

os.makedirs(testCacheDir, exist_ok=True)
os.chdir(testCacheDir)

os.makedirs(join(tmpDir, "pyglossary"), exist_ok=True)


class TestGlossaryBase(unittest.TestCase):
	def __init__(self, *args, **kwargs):
		unittest.TestCase.__init__(self, *args, **kwargs)
		self.maxDiff = None
		self.dataFileCRC32 = {
			"004-bar.txt": "6775e590",
			"004-bar-sort.txt": "fe861123",
			"006-empty.txt": "07ff224b",
			"006-empty-filtered.txt": "2b3c1c0f",
			"100-en-de-v4.txt": "d420a669",
			"100-en-fa.txt": "f5c53133",
			"100-ja-en.txt": "93542e89",
			"100-en-de-v4-remove_font_b.txt": "a3144e2f",
			"100-en-de-v4.sd/100-en-de.dict": "5a97476f",
			"100-en-de-v4.sd/100-en-de.idx": "a99f29d2",
			"100-en-de-v4.sd/100-en-de.ifo": "6529871f",
			"100-en-de-v4.info": "f2cfb284",
			"100-en-fa.info": "9bddb7bb",
			"100-en-fa-v2.info": "7c0f646b",
			"100-ja-en.info": "8cf5403c",
			"300-rand-en-fa.txt": "586617c8",
			"res/stardict.png": "7e1447fa",
			"res/test.json": "41f8cf31",
		}

	def addDirCRC32(self, dirPath: str, files: "dict[str, str]") -> None:
		for fpath, _hash in files.items():
			self.dataFileCRC32[f"{dirPath}/{fpath}"] = _hash

	# The setUp() and tearDown() methods allow you to define instructions that
	# will be executed before and after each test method.

	def setUp(self):
		self.glos = None
		self.tempDir = tempfile.mkdtemp(dir=join(tmpDir, "pyglossary"))

	def tearDown(self):
		if self.glos is not None:
			self.glos.cleanup()
			self.glos.clear()
		if os.getenv("NO_CLEANUP"):
			return
		for direc in (
			self.tempDir,
			appTmpDir,
		):
			if isdir(direc):
				rmtree(direc)

	def fixDownloadFilename(self, filename):
		return filename.replace("/", "__").replace("\\", "__")

	def downloadFile(self, filename):
		unixFilename = filename.replace("\\", "/")
		_crc32 = self.dataFileCRC32[unixFilename]
		fpath = join(testCacheDir, self.fixDownloadFilename(filename))
		if isfile(fpath):
			with open(fpath, mode="rb") as _file:
				data = _file.read()
			if crc32hex(data) != _crc32:
				raise RuntimeError(f"CRC32 check failed for existing file: {fpath!r}")
			return fpath
		try:
			with urlopen(dataURL.format(filename=unixFilename)) as res:
				data = res.read()
		except Exception as e:
			print(f"{filename=}")
			raise e from None
		actual_crc32 = crc32hex(data)
		if actual_crc32 != _crc32:
			raise RuntimeError(
				"CRC32 check failed for downloaded file: "
				f"{filename!r}: {actual_crc32}",
			)
		with open(fpath, mode="wb") as _file:
			_file.write(data)
		return fpath

	def downloadDir(self, dirName: str, files: "list[str]") -> str:
		dirPath = join(testCacheDir, self.fixDownloadFilename(dirName))
		for fileRelPath in files:
			newFilePath = join(dirPath, fileRelPath)
			if isfile(newFilePath):
				# TODO: check crc-32
				continue
			filePath = self.downloadFile(join(dirName, fileRelPath))
			os.makedirs(dirname(newFilePath), exist_ok=True)
			os.rename(filePath, newFilePath)
		return dirPath

	def newTempFilePath(self, filename):
		fpath = join(self.tempDir, filename)
		if isfile(fpath):
			os.remove(fpath)
		return fpath

	def showGlossaryDiff(self, fpath1, fpath2) -> None:
		from pyglossary.ui.tools.diff_glossary import diffGlossary

		diffGlossary(fpath1, fpath2)

	def compareTextFiles(self, fpath1, fpath2, showDiff=False):
		self.assertTrue(isfile(fpath1), f"{fpath1 = }")
		self.assertTrue(isfile(fpath2), f"{fpath2 = }")
		with open(fpath1, encoding="utf-8") as file1:
			text1 = file1.read().rstrip("\n")
		with open(fpath2, encoding="utf-8") as file2:
			text2 = file2.read().rstrip("\n")

		try:
			self.assertEqual(
				len(text1),
				len(text2),
				msg=f"{fpath1!r} differs from {fpath2!r} in file size",
			)
			self.assertEqual(
				text1,
				text2,
				msg=f"{fpath1!r} differs from {fpath2!r}",
			)
		except AssertionError as e:
			if showDiff:
				self.showGlossaryDiff(fpath1, fpath2)
			raise e from None

	def compareBinaryFiles(self, fpath1, fpath2):
		self.assertTrue(isfile(fpath1), f"File {fpath1!r} does not exist")
		self.assertTrue(isfile(fpath2), f"File {fpath2!r} does not exist")
		with open(fpath1, mode="rb") as file1:
			data1 = file1.read()
		with open(fpath2, mode="rb") as file2:
			data2 = file2.read()
		self.assertEqual(len(data1), len(data2), msg=f"{fpath1!r}")
		self.assertTrue(
			data1 == data2,
			msg=f"{fpath1!r} differs from {fpath2!r}",
		)

	def compareZipFiles(
		self,
		fpath1,
		fpath2,
		dataReplaceFuncs: "dict[str, Callable]",
	):
		zf1 = zipfile.ZipFile(fpath1)
		zf2 = zipfile.ZipFile(fpath2)
		pathList1 = zf1.namelist()
		pathList2 = zf2.namelist()
		if not self.assertEqual(pathList1, pathList2):
			return
		for zfpath in pathList1:
			data1 = zf1.read(zfpath)
			data2 = zf2.read(zfpath)

			func = dataReplaceFuncs.get(zfpath)
			if func is not None:
				data1 = func(data1)
				data2 = func(data2)

			self.assertEqual(len(data1), len(data2), msg=f"{zfpath=}")
			self.assertTrue(
				data1 == data2,
				msg=f"{zfpath=}",
			)

	def checkZipFileSha1sum(
		self,
		fpath,
		sha1sumDict: "dict[str, str]",
		dataReplaceFuncs: "Optional[dict[str, Callable]]" = None,
	):
		if dataReplaceFuncs is None:
			dataReplaceFuncs = {}
		zf = zipfile.ZipFile(fpath)
		# pathList = zf.namelist()
		for zfpath, expectedSha1 in sha1sumDict.items():
			data = zf.read(zfpath)
			func = dataReplaceFuncs.get(zfpath)
			if func is not None:
				data = func(data)
			actualSha1 = hashlib.sha1(data).hexdigest()
			self.assertEqual(actualSha1, expectedSha1, msg=f"file: {zfpath}")

	def convert(
		self,
		fname,  # input file with extension
		fname2,  # output file with extension
		testId="tmp",
		compareText="",
		compareBinary="",
		sha1sum=None,
		md5sum=None,
		config=None,
		showDiff=False,
		**convertKWArgs,
	):
		inputFilename = self.downloadFile(fname)
		outputFilename = self.newTempFilePath(fname2)
		glos = self.glos = Glossary()
		if config is not None:
			glos.config = config
		res = glos.convert(
			ConvertArgs(
				inputFilename=inputFilename,
				outputFilename=outputFilename,
				**convertKWArgs,
			),
		)
		self.assertEqual(outputFilename, res)

		if compareText:
			self.compareTextFiles(
				outputFilename,
				self.downloadFile(compareText),
				showDiff=showDiff,
			)
			return

		if compareBinary:
			self.compareBinaryFiles(outputFilename, self.downloadFile(compareBinary))
			return

		msg = f"{outputFilename=}"

		if sha1sum:
			with open(outputFilename, mode="rb") as _file:
				actualSha1 = hashlib.sha1(_file.read()).hexdigest()
			self.assertEqual(sha1sum, actualSha1, msg)
			return

		if md5sum:
			with open(outputFilename, mode="rb") as _file:
				actualMd5 = hashlib.md5(_file.read()).hexdigest()
			self.assertEqual(md5sum, actualMd5, msg)
			return

	def convert_sqlite_both(self, *args, **kwargs):
		for sqlite in (None, True, False):
			self.convert(*args, sqlite=sqlite, **kwargs)


class TestGlossary(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update(
			{
				"100-en-fa-sort.txt": "d7a82dc8",
				"100-en-fa-sort-headword.txt": "4067a29f",
				"100-en-fa-sort-ebook.txt": "aa620d07",
				"100-en-fa-sort-ebook3.txt": "5a20f140",
				"100-en-fa-lower.txt": "62178940",
				"100-en-fa-remove_html_all-v3.txt": "d611c978",
				"100-en-fa-rtl.txt": "25ede1e8",
				"300-rand-en-fa-sort-headword-w1256.txt": "06d83bac",
				"300-rand-en-fa-sort-headword.txt": "df0f8020",
				"300-rand-en-fa-sort-w1256.txt": "9594aab3",
				"sort-locale/092-en-fa-alphabet-sample.txt": "b4856532",
				"sort-locale/092-en-fa-alphabet-sample-sorted-default.txt": "e7b70589",
				"sort-locale/092-en-fa-alphabet-sample-sorted-en.txt": "3d2bdf73",
				"sort-locale/092-en-fa-alphabet-sample-sorted-fa.txt": "245419db",
				"sort-locale/092-en-fa-alphabet-sample-sorted-latin-fa.txt": "261c03c0",
			},
		)

	def setUp(self):
		TestGlossaryBase.setUp(self)
		self.prevLogLevel = log.level
		log.setLevel(logging.ERROR)

	def tearDown(self):
		TestGlossaryBase.tearDown(self)
		log.setLevel(self.prevLogLevel)

	def test__str__1(self):
		glos = self.glos = Glossary()
		self.assertEqual(str(glos), "Glossary{filename: '', name: None}")

	def test__str__2(self):
		glos = self.glos = Glossary()
		glos._filename = "test.txt"
		self.assertEqual(str(glos), "Glossary{filename: 'test.txt', name: None}")

	def test__str__3(self):
		glos = self.glos = Glossary()
		glos.setInfo("title", "Test Title")
		self.assertEqual(
			str(glos),
			"Glossary{filename: '', name: 'Test Title'}",
		)

	def test__str__4(self):
		glos = self.glos = Glossary()
		glos._filename = "test.txt"
		glos.setInfo("title", "Test Title")
		self.assertEqual(
			str(glos),
			"Glossary{filename: 'test.txt', name: 'Test Title'}",
		)

	def test_info_1(self):
		glos = self.glos = Glossary()
		glos.setInfo("test", "ABC")
		self.assertEqual(glos.getInfo("test"), "ABC")

	def test_info_2(self):
		glos = self.glos = Glossary()
		glos.setInfo("bookname", "Test Glossary")
		self.assertEqual(glos.getInfo("title"), "Test Glossary")

	def test_info_3(self):
		glos = self.glos = Glossary()
		glos.setInfo("bookname", "Test Glossary")
		glos.setInfo("title", "Test 2")
		self.assertEqual(glos.getInfo("name"), "Test 2")
		self.assertEqual(glos.getInfo("bookname"), "Test 2")
		self.assertEqual(glos.getInfo("title"), "Test 2")

	def test_info_4(self):
		glos = self.glos = Glossary()
		glos.setInfo("test", 123)
		self.assertEqual(glos.getInfo("test"), "123")

	def test_info_del_1(self):
		glos = self.glos = Glossary()
		glos.setInfo("test", "abc")
		self.assertEqual(glos.getInfo("test"), "abc")
		glos.setInfo("test", None)
		self.assertEqual(glos.getInfo("test"), "")

	def test_info_del_2(self):
		glos = self.glos = Glossary()
		glos.setInfo("test", None)
		self.assertEqual(glos.getInfo("test"), "")

	def test_setInfo_err1(self):
		glos = self.glos = Glossary()
		try:
			glos.setInfo(1, "a")
		except TypeError as e:
			self.assertEqual(str(e), "invalid key=1, must be str")
		else:
			self.fail("must raise a TypeError")

	def test_getInfo_err1(self):
		glos = self.glos = Glossary()
		try:
			glos.getInfo(1)
		except TypeError as e:
			self.assertEqual(str(e), "invalid key=1, must be str")
		else:
			self.fail("must raise a TypeError")

	def test_getExtraInfos_1(self):
		glos = self.glos = Glossary()
		glos.setInfo("a", "test 1")
		glos.setInfo("b", "test 2")
		glos.setInfo("c", "test 3")
		glos.setInfo("d", "test 4")
		glos.setInfo("name", "my name")

		self.assertEqual(
			glos.getExtraInfos(["b", "c", "title"]),
			{"a": "test 1", "d": "test 4"},
		)

	def test_infoKeys_1(self):
		glos = self.glos = Glossary()
		glos.setInfo("a", "test 1")
		glos.setInfo("b", "test 2")
		glos.setInfo("name", "test name")
		glos.setInfo("title", "test title")

		self.assertEqual(
			glos.infoKeys(),
			["a", "b", "name"],
		)

	def test_config_attr_get(self):
		glos = self.glos = Glossary()
		try:
			glos.config  # noqa: B018
		except NotImplementedError:
			pass
		else:
			self.fail("must raise NotImplementedError")

	def test_config_attr_set(self):
		glos = self.glos = Glossary()
		glos.config = {"lower": True}
		self.assertEqual(glos.getConfig("lower", False), True)

	def test_directRead_txt_1(self):
		inputFilename = self.downloadFile("100-en-fa.txt")
		glos = self.glos = Glossary()
		res = glos.directRead(filename=inputFilename)
		self.assertTrue(res)
		self.assertEqual(glos.sourceLangName, "English")
		self.assertEqual(glos.targetLangName, "Persian")
		self.assertIn("Sample: ", glos.getInfo("name"))

		entryCount = sum(1 for _ in glos)
		self.assertEqual(entryCount, 100)

	def test_init_infoDict(self):
		glos = self.glos = Glossary(info={"a": "b"})
		self.assertEqual(list(glos.iterInfo()), [("a", "b")])

	def test_init_infoOrderedDict(self):
		from collections import OrderedDict

		glos = self.glos = Glossary(
			info=OrderedDict(
				[
					("y", "z"),
					("a", "b"),
					("1", "2"),
				],
			),
		)
		self.assertEqual(list(glos.iterInfo()), [("y", "z"), ("a", "b"), ("1", "2")])

	def test_lang_1(self):
		glos = self.glos = Glossary()
		self.assertEqual(glos.sourceLangName, "")
		self.assertEqual(glos.targetLangName, "")
		glos.sourceLangName = "ru"
		glos.targetLangName = "de"
		self.assertEqual(glos.sourceLangName, "Russian")
		self.assertEqual(glos.targetLangName, "German")

	def test_lang_get_source(self):
		glos = self.glos = Glossary()
		glos.setInfo("sourcelang", "farsi")
		self.assertEqual(glos.sourceLangName, "Persian")

	def test_lang_get_target(self):
		glos = self.glos = Glossary()
		glos.setInfo("targetlang", "malay")
		self.assertEqual(glos.targetLangName, "Malay")

	def test_lang_set_source(self):
		glos = self.glos = Glossary()
		glos.sourceLangName = "en"
		self.assertEqual(glos.sourceLangName, "English")

	def test_lang_set_source_empty(self):
		glos = self.glos = Glossary()
		glos.sourceLangName = ""
		self.assertEqual(glos.sourceLangName, "")

	def test_lang_set_target(self):
		glos = self.glos = Glossary()
		glos.targetLangName = "fa"
		self.assertEqual(glos.targetLangName, "Persian")

	def test_lang_set_target_empty(self):
		glos = self.glos = Glossary()
		glos.targetLangName = ""
		self.assertEqual(glos.targetLangName, "")

	def test_lang_getObj_source(self):
		glos = self.glos = Glossary()
		glos.setInfo("sourcelang", "farsi")
		self.assertEqual(glos.sourceLang.name, "Persian")

	def test_lang_getObj_target(self):
		glos = self.glos = Glossary()
		glos.setInfo("targetlang", "malay")
		self.assertEqual(glos.targetLang.name, "Malay")

	def test_lang_detect_1(self):
		glos = self.glos = Glossary()
		glos.setInfo("name", "en-fa")
		glos.detectLangsFromName()
		self.assertEqual(
			(glos.sourceLangName, glos.targetLangName),
			("English", "Persian"),
		)

	def test_lang_detect_2(self):
		glos = self.glos = Glossary()
		glos.setInfo("name", "test-en-fa")
		glos.detectLangsFromName()
		self.assertEqual(
			(glos.sourceLangName, glos.targetLangName),
			("English", "Persian"),
		)

	def test_lang_detect_3(self):
		glos = self.glos = Glossary()
		glos.setInfo("name", "eng to per")
		glos.detectLangsFromName()
		self.assertEqual(
			(glos.sourceLangName, glos.targetLangName),
			("English", "Persian"),
		)

	def test_lang_detect_4(self):
		glos = self.glos = Glossary()
		glos.setInfo("name", "Test english to farsi")
		glos.detectLangsFromName()
		self.assertEqual(
			(glos.sourceLangName, glos.targetLangName),
			("English", "Persian"),
		)

	def test_lang_detect_5(self):
		glos = self.glos = Glossary()
		glos.setInfo("name", "freedict-eng-deu.index")
		glos.detectLangsFromName()
		self.assertEqual(
			(glos.sourceLangName, glos.targetLangName),
			("English", "German"),
		)

	def convert_txt_txt(
		self,
		fname,  # input txt file without extension
		fname2,  # expected output txt file without extension
		testId="tmp",
		config=None,
		**convertArgs,
	):
		self.convert(
			f"{fname}.txt",
			f"{fname2}-{testId}.txt",
			compareText=f"{fname2}.txt",
			testId=testId,
			config=config,
			**convertArgs,
		)

	def convert_to_txtZip(
		self,
		fname,  # input file with extension
		fname2,  # expected output file without extensions
		testId="tmp",
		config=None,
		**convertKWArgs,
	):
		inputFilename = self.downloadFile(fname)
		outputTxtName = f"{fname2}-{testId}.txt"
		outputFilename = self.newTempFilePath(f"{outputTxtName}.zip")
		expectedFilename = self.downloadFile(f"{fname2}.txt")
		glos = self.glos = Glossary()
		if config is not None:
			glos.config = config
		res = glos.convert(
			ConvertArgs(
				inputFilename=inputFilename,
				outputFilename=outputFilename,
				**convertKWArgs,
			),
		)
		self.assertEqual(outputFilename, res)
		zf = zipfile.ZipFile(outputFilename)
		self.assertTrue(
			outputTxtName in zf.namelist(),
			msg=f"{outputTxtName} not in {zf.namelist()}",
		)
		with open(expectedFilename, encoding="utf-8") as expectedFile:
			expectedText = expectedFile.read()
		actualText = zf.read(outputTxtName).decode("utf-8")
		self.assertEqual(len(actualText), len(expectedText))
		self.assertEqual(actualText, expectedText)

	def test_txt_txtZip_1(self):
		self.convert_to_txtZip(
			"100-en-fa.txt",
			"100-en-fa",
			testId="txt_txtZip_1",
			infoOverride={"input_file_size": None},
		)

	def test_sort_1(self):
		self.convert_txt_txt(
			"100-en-fa",
			"100-en-fa-sort",
			testId="sort_1",
			sort=True,
		)

	def test_sort_2(self):
		self.convert_txt_txt(
			"100-en-fa",
			"100-en-fa-sort",
			testId="sort_2",
			sort=True,
			sortKeyName="headword_lower",
		)

	def test_sort_3(self):
		self.convert_txt_txt(
			"100-en-fa",
			"100-en-fa-sort-headword",
			testId="sort_3",
			sort=True,
			sortKeyName="headword",
		)

	def test_sort_4(self):
		self.convert_txt_txt(
			"300-rand-en-fa",
			"300-rand-en-fa-sort-headword",
			testId="sort_4",
			sort=True,
			sortKeyName="headword",
		)

	def test_sort_5(self):
		self.convert_txt_txt(
			"300-rand-en-fa",
			"300-rand-en-fa-sort-headword-w1256",
			testId="sort_5",
			sort=True,
			sortKeyName="headword",
			sortEncoding="windows-1256",
		)

	def test_sort_6(self):
		self.convert_txt_txt(
			"300-rand-en-fa",
			"300-rand-en-fa-sort-w1256",
			testId="sort_6",
			sort=True,
			sortKeyName="headword_lower",
			sortEncoding="windows-1256",
		)

	def test_sort_7(self):
		self.convert_txt_txt(
			"100-en-fa",
			"100-en-fa-sort-ebook",
			testId="sort_7",
			sort=True,
			sortKeyName="ebook",
		)

	def test_sort_8(self):
		self.convert_txt_txt(
			"100-en-fa",
			"100-en-fa-sort-ebook3",
			testId="sort_8",
			sort=True,
			sortKeyName="ebook_length3",
		)

	def test_lower_1(self):
		self.convert_txt_txt(
			"100-en-fa",
			"100-en-fa-lower",
			testId="lower_1",
			config={"lower": True},
		)

	def test_rtl_1(self):
		self.convert_txt_txt(
			"100-en-fa",
			"100-en-fa-rtl",
			testId="rtl_1",
			config={"rtl": True},
		)

	def test_remove_html_all_1(self):
		self.convert_txt_txt(
			"100-en-fa",
			"100-en-fa-remove_html_all-v3",
			testId="remove_html_all_1",
			config={"remove_html_all": True},
		)

	def test_remove_html_1(self):
		self.convert_txt_txt(
			"100-en-de-v4",
			"100-en-de-v4-remove_font_b",
			testId="remove_html_1",
			config={"remove_html": "font,b"},
		)

	def test_save_info_json(self):
		fname = "100-en-fa"
		testId = "save_info_json"
		infoPath = self.newTempFilePath(f"{fname}-{testId}.info")
		self.convert_txt_txt(
			fname,
			fname,
			testId=testId,
			config={"save_info_json": True},
			infoOverride={"input_file_size": None},
		)
		self.compareTextFiles(
			infoPath,
			self.downloadFile(f"{fname}-v2.info"),
		)

	def test_convert_sqlite_direct_error(self):
		glos = self.glos = Glossary()
		try:
			glos.convert(
				ConvertArgs(
					inputFilename="foo.txt",
					outputFilename="bar.txt",
					direct=True,
					sqlite=True,
				),
			)
		except ValueError as e:
			self.assertEqual(str(e), "Conflictng arguments: direct=True, sqlite=True")
		else:
			self.fail("must raise a ValueError")

	def test_txt_txt_bar(self):
		for direct in (None, False, True):
			self.convert_txt_txt(
				"004-bar",
				"004-bar",
				testId="bar",
				direct=direct,
				infoOverride={
					"name": None,
					"input_file_size": None,
				},
			)

	def test_txt_txt_bar_sort(self):
		for sqlite in (None, False, True):
			self.convert_txt_txt(
				"004-bar",
				"004-bar-sort",
				testId="bar_sort",
				sort=True,
				sqlite=sqlite,
			)

	def test_txt_txt_empty_filtered(self):
		for direct in (None, False, True):
			self.convert_txt_txt(
				"006-empty",
				"006-empty-filtered",
				testId="empty_filtered",
				direct=direct,
			)

	def test_txt_txt_empty_filtered_sqlite(self):
		for sqlite in (None, False, True):
			self.convert_txt_txt(
				"006-empty",
				"006-empty-filtered",
				testId="empty_filtered_sqlite",
				sqlite=sqlite,
			)

	def test_dataEntry_save(self):
		glos = self.glos = Glossary()
		tmpFname = "test_dataEntry_save"
		entry = glos.newDataEntry(tmpFname, b"test")
		saveFpath = entry.save(self.tempDir)
		self.assertTrue(
			isfile(saveFpath),
			msg=f"saved file does not exist: {saveFpath}",
		)

	def test_dataEntry_getFileName(self):
		glos = self.glos = Glossary()
		tmpFname = "test_dataEntry_getFileName"
		entry = glos.newDataEntry(tmpFname, b"test")
		self.assertEqual(entry.getFileName(), tmpFname)

	def test_cleanup_noFile(self):
		glos = self.glos = Glossary()
		glos.cleanup()

	def test_cleanup_cleanup(self):
		glos = self.glos = Glossary()
		tmpFname = "test_cleanup_cleanup"
		entry = glos.newDataEntry(tmpFname, b"test")

		tmpFpath = entry._tmpPath
		self.assertTrue(bool(tmpFpath), msg="entry tmpPath is empty")
		self.assertTrue(
			isfile(tmpFpath),
			msg=f"tmp file does not exist: {tmpFpath}",
		)

		glos.cleanup()

		self.assertTrue(
			not isfile(tmpFpath),
			msg=f"tmp file still exists: {tmpFpath}",
		)

	def test_cleanup_noCleanup(self):
		glos = self.glos = Glossary()
		tmpFname = "test_cleanup_noCleanup"
		entry = glos.newDataEntry(tmpFname, b"test")

		tmpFpath = entry._tmpPath
		self.assertTrue(bool(tmpFpath), msg="entry tmpPath is empty")
		self.assertTrue(isfile(tmpFpath), msg=f"tmp file does not exist: {tmpFpath}")

		glos.config = {"cleanup": False}
		glos.cleanup()

		self.assertTrue(isfile(tmpFpath), msg=f"tmp file does not exist: {tmpFpath}")

	def test_rawEntryCompress(self):
		glos = self.glos = Glossary()
		glos.setRawEntryCompress(True)
		self.assertTrue(glos.rawEntryCompress)
		glos.setRawEntryCompress(False)
		self.assertFalse(glos.rawEntryCompress)

	def addWordsList(self, glos, words, newDefiFunc=str, defiFormat=""):
		wordsList = []
		for index, line in enumerate(words):
			words = line.rstrip().split("|")
			wordsList.append(words)
			glos.addEntry(
				glos.newEntry(
					words,
					newDefiFunc(index),
					defiFormat=defiFormat,
				),
			)

		return wordsList

	def addWords(self, glos, wordsStr, **kwargs):
		return self.addWordsList(glos, wordsStr.split("\n"), **kwargs)

	tenWordsStr = """comedic
tubenose
organosol
adipocere
gid
next friend
bitter apple
caca|ca-ca
darkling beetle
japonica"""

	tenWordsStr2 = """comedic
Tubenose
organosol
Adipocere
gid
Next friend
bitter apple
Caca|ca-ca
darkling beetle
Japonica"""

	tenWordsStrFa = (
		"بیمارانه\nگالوانومتر\nنقاهت\nرشک"
		"مندی\nناکاستنی\nشگفتآفرینی\nچندپاری\nنامبارکی\nآماسش\nانگیزنده"
	)

	def test_addEntries_1(self):
		glos = self.glos = Glossary()
		wordsList = self.addWords(
			glos,
			self.tenWordsStr,
			newDefiFunc=lambda i: str(random.randint(0, 10000)),
		)
		self.assertEqual(wordsList, [entry.l_word for entry in glos])

	def test_addEntries_2(self):
		# entry filters don't apply to loaded entries (added with addEntry)
		glos = self.glos = Glossary()
		glos.addEntry(glos.newEntry(["a"], "test 1"))
		glos.addEntry(glos.newEntry([""], "test 2"))
		glos.addEntry(glos.newEntry(["b"], "test 3"))
		glos.addEntry(glos.newEntry([], "test 4"))
		glos.updateEntryFilters()
		self.assertEqual(
			[["a"], [""], ["b"], []],
			[entry.l_word for entry in glos],
		)

	def test_addEntries_3(self):
		glos = self.glos = Glossary()
		glos.addEntry(glos.newEntry(["a"], "test 1"))
		glos.addEntry(glos.newEntry(["b"], "test 3"))
		glos.addEntry(
			glos.newDataEntry(
				"file.bin",
				b"hello\x00world",
			),
		)
		glos.updateEntryFilters()
		wordListList = []
		dataEntries = []
		for entry in glos:
			wordListList.append(entry.l_word)
			if entry.isData():
				dataEntries.append(entry)
		self.assertEqual(
			wordListList,
			[["a"], ["b"], ["file.bin"]],
		)
		self.assertEqual(len(dataEntries), 1)
		self.assertEqual(dataEntries[0].getFileName(), "file.bin")
		self.assertEqual(dataEntries[0].data, b"hello\x00world")

	def test_read_filename(self):
		glos = self.glos = Glossary()
		glos.directRead(self.downloadFile("004-bar.txt"))
		self.assertEqual(glos.filename, join(testCacheDir, "004-bar"))

	def test_wordTitleStr_em1(self):
		glos = self.glos = Glossary()
		self.assertEqual(glos.wordTitleStr(""), "")

	def test_wordTitleStr_em2(self):
		glos = self.glos = Glossary()
		glos._defiHasWordTitle = True
		self.assertEqual(glos.wordTitleStr("test1"), "")

	def test_wordTitleStr_b1(self):
		glos = self.glos = Glossary()
		self.assertEqual(glos.wordTitleStr("test1"), "<b>test1</b><br>")

	def test_wordTitleStr_b2(self):
		glos = self.glos = Glossary()
		self.assertEqual(
			glos.wordTitleStr("test1", _class="headword"),
			'<b class="headword">test1</b><br>',
		)

	def test_wordTitleStr_cjk1(self):
		glos = self.glos = Glossary()
		self.assertEqual(
			glos.wordTitleStr("test1", sample="くりかえし"),
			"<big>test1</big><br>",
		)

	def test_wordTitleStr_cjk2(self):
		glos = self.glos = Glossary()
		self.assertEqual(
			glos.wordTitleStr("くりかえし"),
			"<big>くりかえし</big><br>",
		)

	def test_convert_sortLocale_default_1(self):
		name = "092-en-fa-alphabet-sample"
		self.convert_sqlite_both(
			f"sort-locale/{name}.txt",
			f"{name}-sorted-default.txt",
			compareText=f"sort-locale/{name}-sorted-default.txt",
			testId="sorted-default",
			sort=True,
			sortKeyName="headword_lower",
		)

	def test_convert_sortLocale_en_1(self):
		name = "092-en-fa-alphabet-sample"
		self.convert_sqlite_both(
			f"sort-locale/{name}.txt",
			f"{name}-sorted-en.txt",
			compareText=f"sort-locale/{name}-sorted-en.txt",
			testId="sorted-en",
			sort=True,
			sortKeyName="headword_lower:en_US.UTF-8",
		)

	def test_convert_sortLocale_fa_1(self):
		name = "092-en-fa-alphabet-sample"
		self.convert_sqlite_both(
			f"sort-locale/{name}.txt",
			f"{name}-sorted-fa.txt",
			compareText=f"sort-locale/{name}-sorted-fa.txt",
			testId="sorted-fa",
			sort=True,
			sortKeyName="headword_lower:fa_IR.UTF-8",
		)

	def test_convert_sortLocale_fa_2(self):
		name = "092-en-fa-alphabet-sample"
		self.convert_sqlite_both(
			f"sort-locale/{name}.txt",
			f"{name}-sorted-latin-fa.txt",
			compareText=f"sort-locale/{name}-sorted-latin-fa.txt",
			testId="sorted-latin-fa",
			sort=True,
			sortKeyName="headword_lower:fa-u-kr-latn-arab",
		)


if __name__ == "__main__":
	unittest.main()
