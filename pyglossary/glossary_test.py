#!/usr/bin/python3

import sys
import os
from os.path import join, dirname, abspath, isdir, isfile
import unittest
import tempfile
from urllib.request import urlopen

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.glossary import Glossary, log
from pyglossary.entry import Entry
from pyglossary.core import cacheDir
from pyglossary.os_utils import rmtree
from pyglossary.text_utils import crc32hex

Glossary.init()


dataURL = (
	"https://raw.githubusercontent.com/"
	"ilius/pyglossary-test/main/{filename}"
)

dataDir = join(cacheDir, "test")


class TestGlossaryBase(unittest.TestCase):
	def __init__(self, *args, **kwargs):
		unittest.TestCase.__init__(self, *args, **kwargs)
		self.maxDiff = None
		log.setVerbosity(1)
		self.dataFileCRC32 = {
			"004-bar.txt": "6775e590",
			"100-en-de.txt": "f22fc392",
			"100-en-fa.txt": "f5c53133",
			"100-ja-en.txt": "93542e89",

			"res/stardict.png": "7e1447fa",
			"res/test.json": "41f8cf31",
		}

	# The setUp() and tearDown() methods allow you to define instructions that
	# will be executed before and after each test method.

	def setUp(self):
		if not isdir(dataDir):
			os.makedirs(dataDir)
		self.tempDir = tempfile.mkdtemp(dir=dataDir)

	def tearDown(self):
		if os.getenv("NO_CLEANUP"):
			return
		rmtree(self.tempDir)

	def downloadFile(self, filename):
		_crc32 = self.dataFileCRC32[filename]
		fpath = join(dataDir, filename.replace("/", "__"))
		if isfile(fpath):
			with open(fpath, mode="rb") as _file:
				data = _file.read()
			if crc32hex(data) != _crc32:
				raise RuntimeError(f"CRC32 check failed for existing file: {fpath}")
			return fpath
		try:
			with urlopen(dataURL.format(filename=filename)) as res:
				data = res.read()
		except Exception as e:
			e.msg += f", filename={filename}"
			raise e
		if crc32hex(data) != _crc32:
			raise RuntimeError(f"CRC32 check failed for downloaded file: {filename}")
		with open(fpath, mode="wb") as _file:
			_file.write(data)
		return fpath

	def newTempFilePath(self, filename):
		fpath = join(self.tempDir, filename)
		if isfile(fpath):
			os.remove(fpath)
		return fpath

	def compareTextFiles(self, fpath1, fpath2):
		self.assertTrue(isfile(fpath1))
		self.assertTrue(isfile(fpath2))
		with open(fpath1) as file1:
			with open(fpath2) as file2:
				text1 = file1.read()
				text2 = file2.read()
				self.assertEqual(
					text1,
					text2,
					msg=f"{fpath1} differs from {fpath2}",
				)

	def compareBinaryFiles(self, fpath1, fpath2):
		self.assertTrue(isfile(fpath1), f"File {fpath1} does not exist")
		self.assertTrue(isfile(fpath2), f"File {fpath2} does not exist")
		with open(fpath1, mode="rb") as file1:
			with open(fpath2, mode="rb") as file2:
				data1 = file1.read()
				data2 = file2.read()
				self.assertEqual(len(data1), len(data2), msg=f"{fpath1}")
				self.assertTrue(
					data1 == data2,
					msg=f"{fpath1} differs from {fpath2}",
				)

	def compareZipFiles(
		self,
		fpath1,
		fpath2,
		dataReplaceFuncs: "Dict[str: Callable",
	):
		import zipfile
		zf1 = zipfile.ZipFile(fpath1)
		zf2 = zipfile.ZipFile(fpath2)
		pathList1 = zf1.namelist()
		pathList2 = zf1.namelist()
		self.assertEqual(pathList1, pathList2)
		for zfpath in pathList1:
			data1 = zf1.read(zfpath)
			data2 = zf2.read(zfpath)

			func = dataReplaceFuncs.get(zfpath)
			if func is not None:
				data1 = func(data1)
				data2 = func(data2)

			self.assertEqual(len(data1), len(data2), msg=f"zfpath={zfpath!r}")
			self.assertTrue(
				data1 == data2,
				msg=f"zfpath={zfpath!r}",
			)


class TestGlossary(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update({
			"100-en-de.csv": "b5283518",
			"100-en-fa.csv": "eb8b0474",
			"100-ja-en.csv": "7af18cf3",


			"100-en-fa-sort.txt": "d7a82dc8",
			"100-en-fa-lower.txt": "62178940",
			"100-en-fa-remove_html_all.txt": "d611c978",
			"100-en-fa-rtl.txt": "25ede1e8",
			"100-en-de-remove_font_b.txt": "727320ac",
		})


	def test_read_txt_1(self):
		inputFilename = self.downloadFile("100-en-fa.txt")
		glos = Glossary()
		res = glos.read(filename=inputFilename)
		self.assertTrue(res)
		self.assertEqual(glos.sourceLangName, "English")
		self.assertEqual(glos.targetLangName, "Persian")
		self.assertIn("Sample: ", glos.getInfo("name"))

	def test_langs(self):
		glos = Glossary()
		self.assertEqual(glos.sourceLangName, "")
		self.assertEqual(glos.targetLangName, "")
		glos.sourceLangName = "ru"
		glos.targetLangName = "de"
		self.assertEqual(glos.sourceLangName, "Russian")
		self.assertEqual(glos.targetLangName, "German")

	def convert_txt_csv(self, fname):
		inputFilename = self.downloadFile(f"{fname}.txt")
		outputFilename = self.newTempFilePath(f"{fname}-2.csv")
		expectedFilename = self.downloadFile(f"{fname}.csv")
		glos = Glossary()
		res = glos.convert(
			inputFilename=inputFilename,
			outputFilename=outputFilename,
		)
		self.assertEqual(outputFilename, res)
		self.compareTextFiles(outputFilename, expectedFilename)

	def convert_csv_txt_rw(self, fname):
		inputFilename = self.downloadFile(f"{fname}.csv")
		outputFilename = self.newTempFilePath(f"{fname}-2.txt")
		expectedFilename = self.downloadFile(f"{fname}.txt")
		glos = Glossary()
		# using glos.convert will add "input_file_size" info key
		# perhaps add another optional argument to glos.convert named infoOverride

		rRes = glos.read(inputFilename, direct=True)
		self.assertTrue(rRes)

		glos.setInfo("input_file_size", None)

		wRes = glos.write(outputFilename, format="Tabfile")
		self.assertEqual(outputFilename, wRes)

		self.compareTextFiles(outputFilename, expectedFilename)

	def convert_csv_txt(self, fname):
		inputFilename = self.downloadFile(f"{fname}.csv")
		outputFilename = self.newTempFilePath(f"{fname}-2.txt")
		expectedFilename = self.downloadFile(f"{fname}.txt")
		glos = Glossary()

		res = glos.convert(
			inputFilename=inputFilename,
			outputFilename=outputFilename,
			infoOverride={
				"input_file_size": None,
			},
		)
		self.assertEqual(outputFilename, res)

		self.compareTextFiles(outputFilename, expectedFilename)

	def convert_txt_txt(self, fname, fname2, config=None, **convertArgs):
		inputFilename = self.downloadFile(f"{fname}.txt")
		outputFilename = self.newTempFilePath(f"{fname2}-tmp.txt")
		expectedFilename = self.downloadFile(f"{fname2}.txt")
		glos = Glossary()

		if config is not None:
			glos.config = config

		res = glos.convert(
			inputFilename=inputFilename,
			outputFilename=outputFilename,
			**convertArgs
		)
		self.assertEqual(outputFilename, res)

		self.compareTextFiles(outputFilename, expectedFilename)


	def test_convert_txt_csv_1(self):
		self.convert_txt_csv("100-en-fa")

	def test_convert_txt_csv_2(self):
		self.convert_txt_csv("100-en-de")

	def test_convert_txt_csv_3(self):
		self.convert_txt_csv("100-ja-en")

	def test_convert_csv_txt_1(self):
		self.convert_csv_txt("100-en-fa")

	def test_convert_csv_txt_2(self):
		self.convert_csv_txt("100-en-de")

	def test_convert_csv_txt_3(self):
		self.convert_csv_txt("100-ja-en")

	def test_convert_csv_txt_4(self):
		self.convert_csv_txt_rw("100-en-fa")

	def test_convert_txt_txt_sort_1(self):
		self.convert_txt_txt(
			"100-en-fa",
			"100-en-fa-sort",
			sort=True,
			defaultSortKey=Entry.defaultSortKey,
		)

	def test_convert_txt_txt_lower_1(self):
		self.convert_txt_txt(
			"100-en-fa",
			"100-en-fa-lower",
			{"lower": True},
		)

	def test_convert_txt_txt_rtl_1(self):
		self.convert_txt_txt(
			"100-en-fa",
			"100-en-fa-rtl",
			{"rtl": True},
		)

	def test_convert_txt_txt_remove_html_all_1(self):
		self.convert_txt_txt(
			"100-en-fa",
			"100-en-fa-remove_html_all",
			{"remove_html_all": True},
		)

	def test_convert_txt_txt_remove_html_1(self):
		self.convert_txt_txt(
			"100-en-de",
			"100-en-de-remove_font_b",
			{"remove_html": "font,b"},
		)


	def test_convert_sqlite_direct_error(self):
		glos = Glossary()
		err = ""
		try:
			res = glos.convert(
				inputFilename="foo.txt",
				outputFilename="bar.txt",
				direct=True,
				sqlite=True,
			)
		except Exception as e:
			err = str(e)
			res = ""
		self.assertEqual(res, "")
		self.assertEqual(err, "Conflictng arguments: direct=True, sqlite=True")


if __name__ == "__main__":
	unittest.main()
