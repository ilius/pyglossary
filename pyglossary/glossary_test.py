#!/usr/bin/python3

import sys
import os
from os.path import join, dirname, abspath, isdir, isfile
import unittest
import random
from urllib.request import urlopen

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.glossary import Glossary, log
from pyglossary.entry import Entry
from pyglossary.core import tmpDir, cacheDir
from pyglossary.os_utils import rmtree
from pyglossary.text_utils import crc32hex

Glossary.init()


dataURL = (
	"https://raw.githubusercontent.com/"
	"ilius/pyglossary-test/main/{filename}"
)

dataDir = join(cacheDir, "test")

dataFileCRC32 = {
	"004-bar.txt": "6775e590",
	"004-bar.json": "7e4b2663",
	"004-bar.sd/004-bar.dict": "9ea397f8",
	"004-bar.sd/004-bar.idx": "cf9440cf",
	"004-bar.sd/004-bar.ifo": "ada870e4",
	"004-bar.sd/004-bar.syn": "286b17bf",

	"100-en-de.txt": "f22fc392",
	"100-en-de.csv": "b5283518",
	"100-en-de.json": "6fa8e159",
	"100-en-de.sd/100-en-de.dict": "d74bf277",
	"100-en-de.sd/100-en-de.idx": "945b303c",
	"100-en-de.sd/100-en-de.ifo": "6529871f",
	"100-en-de-remove_font_b.txt": "727320ac",

	"100-en-fa.txt": "f5c53133",
	"100-en-fa-sort.txt": "d7a82dc8",
	"100-en-fa.csv": "eb8b0474",
	"100-en-fa.json": "8d29c1be",
	"100-en-fa-lower.txt": "62178940",
	"100-en-fa-remove_html_all.txt": "d611c978",
	"100-en-fa-rtl.txt": "25ede1e8",
	"100-en-fa.sd/100-en-fa.dict": "223a0d1d",
	"100-en-fa.sd/100-en-fa.idx": "6df43378",
	"100-en-fa.sd/100-en-fa.ifo": "3f2086cd",
	"100-en-fa.sd/100-en-fa.syn": "1160fa0b",
	"100-en-fa-res.slob": "0216d006",
	"100-en-fa-res-slob.txt": "c73100b3",
	"100-en-fa-res-slob-sort.txt": "8253fe96",
	"100-en-fa-res-slob.epub": "30506767",

	"res/stardict.png": "7e1447fa",
	"res/test.json": "41f8cf31",

	"100-ja-en.txt": "93542e89",
	"100-ja-en.csv": "7af18cf3",
	"100-ja-en.json": "fab2c106",
	"100-ja-en.sd/100-ja-en.dict": "39715f01",
	"100-ja-en.sd/100-ja-en.idx": "adf0e552",
	"100-ja-en.sd/100-ja-en.ifo": "b01e368c",
	"100-ja-en.sd/100-ja-en.syn": "76e6df95",
}


class TestGlossary(unittest.TestCase):
	def __init__(self, *args, **kwargs):
		unittest.TestCase.__init__(self, *args, **kwargs)
		self.maxDiff = None
		self._cleanupPathList = set()
		log.setVerbosity(1)

	def setUp(self):
		if not isdir(dataDir):
			os.makedirs(dataDir)

	def tearDown(self):
		if os.getenv("NO_CLEANUP"):
			return
		for cleanupPath in self._cleanupPathList:
			if isfile(cleanupPath):
				log.debug(f"Removing file {cleanupPath}")
				try:
					os.remove(cleanupPath)
				except Exception:
					log.exception(f"error removing {cleanupPath}")
			elif isdir(cleanupPath):
				log.debug(f"Removing directory {cleanupPath}")
				rmtree(cleanupPath)
			else:
				log.error(f"no such file or directory: {cleanupPath}")

	def downloadFile(self, filename):
		_crc32 = dataFileCRC32[filename]
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
		fpath = join(dataDir, filename)
		self._cleanupPathList.add(fpath)
		if isfile(fpath):
			os.remove(fpath)
		return fpath

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

	def convert_txt_json(self, fname):
		inputFilename = self.downloadFile(f"{fname}.txt")
		outputFilename = self.newTempFilePath(f"{fname}-2.json")
		expectedFilename = self.downloadFile(f"{fname}.json")
		glos = Glossary()
		res = glos.convert(
			inputFilename=inputFilename,
			outputFilename=outputFilename,
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

	def test_convert_txt_json_0(self):
		self.convert_txt_json("004-bar")

	def test_convert_txt_json_1(self):
		self.convert_txt_json("100-en-fa")

	def test_convert_txt_json_2(self):
		self.convert_txt_json("100-en-de")

	def test_convert_txt_json_3(self):
		self.convert_txt_json("100-ja-en")

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

	def convert_txt_stardict(
		self,
		fname,
		syn=True,
		dictzip=False,
		config=None,
		rawEntryCompress=None,
		**kwargs
	):
		binExtList = ["idx", "dict"]
		if syn:
			binExtList.append("syn")

		inputFilename = self.downloadFile(f"{fname}.txt")
		outputFilename = self.newTempFilePath(f"{fname}.ifo")
		otherFiles = {
			ext: self.newTempFilePath(f"{fname}.{ext}")
			for ext in binExtList
		}

		glos = Glossary()

		if config is not None:
			glos.config = config

		if rawEntryCompress is not None:
			glos.setRawEntryCompress(rawEntryCompress)

		res = glos.convert(
			inputFilename=inputFilename,
			outputFilename=outputFilename,
			writeOptions={
				"dictzip": dictzip,
			},
			**kwargs
		)
		self.assertEqual(outputFilename, res)

		self.compareTextFiles(
			outputFilename,
			self.downloadFile(f"{fname}.sd/{fname}.ifo"),
		)

		for ext in binExtList:
			self.compareBinaryFiles(
				otherFiles[ext],
				self.downloadFile(f"{fname}.sd/{fname}.{ext}")
			)

	def test_convert_txt_stardict_1(self):
		for sqlite in (None, False, True):
			for rawEntryCompress in (None, True, False):
				self.convert_txt_stardict(
					"100-en-fa",
					rawEntryCompress=rawEntryCompress,
					sqlite=sqlite,
				)

	def test_convert_txt_stardict_2(self):
		for sqlite in (None, False, True):
			for rawEntryCompress in (None, True, False):
				self.convert_txt_stardict(
					"004-bar",
					rawEntryCompress=rawEntryCompress,
					sqlite=sqlite,
				)

	def test_convert_txt_stardict_3(self):
		for sqlite in (None, False, True):
			self.convert_txt_stardict(
				"100-en-de",
				syn=False,
				sqlite=sqlite,
			)

	def test_convert_txt_stardict_4(self):
		for sqlite in (None, False, True):
			self.convert_txt_stardict(
				"100-ja-en",
				sqlite=sqlite,
			)

	def test_convert_txt_stardict_sqlite_no_alts(self):
		self.convert_txt_stardict(
			"100-en-fa",
			config={"enable_alts": False},
			sqlite=True,
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

	def test_convert_txt_slob_1(self):
		fname = "100-en-fa"
		inputFilename = self.downloadFile(f"{fname}.txt")
		outputFilename = self.newTempFilePath(f"{fname}.slob")
		glos = Glossary()
		outputFilename2 = glos.convert(
			inputFilename=inputFilename,
			outputFilename=outputFilename,
		)
		self.assertEqual(outputFilename, outputFilename2)

	def convert_slob_txt(self, fname, fname2, resFiles, **convertArgs):
		inputFilename = self.downloadFile(f"{fname}.slob")
		outputFilename = self.newTempFilePath(f"{fname}-2.txt")

		resFilesPath = {
			resFileName: self.newTempFilePath(f"{fname}-2.txt_res/{resFileName}")
			for resFileName in resFiles
		}

		expectedFilename = self.downloadFile(f"{fname2}.txt")
		glos = Glossary()
		res = glos.convert(
			inputFilename=inputFilename,
			outputFilename=outputFilename,
			**convertArgs
		)
		self.assertEqual(outputFilename, res)
		self.compareTextFiles(outputFilename, expectedFilename)

		for resFileName in resFiles:
			fpath1 = self.downloadFile(f"res/{resFileName}")
			fpath2 = resFilesPath[resFileName]
			self.compareBinaryFiles(fpath1, fpath2)

	def test_convert_slob_txt_1(self):
		self.convert_slob_txt(
			"100-en-fa-res",
			"100-en-fa-res-slob",
			resFiles=[
				"stardict.png",
				"test.json",
			],
		)

	def test_convert_slob_txt_2(self):
		self.convert_slob_txt(
			"100-en-fa-res",
			"100-en-fa-res-slob",
			resFiles=[
				"stardict.png",
				"test.json",
			],
			direct=False,
		)

	def test_convert_slob_txt_2(self):
		self.convert_slob_txt(
			"100-en-fa-res",
			"100-en-fa-res-slob",
			resFiles=[
				"stardict.png",
				"test.json",
			],
			sqlite=True,
		)

	def test_convert_slob_txt_2(self):
		self.convert_slob_txt(
			"100-en-fa-res",
			"100-en-fa-res-slob-sort",
			resFiles=[
				"stardict.png",
				"test.json",
			],
			sort=True,
			defaultSortKey=Entry.defaultSortKey,
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

	def convert_slob_epub(self, fname, fname2, **convertArgs):
		import re

		inputFilename = self.downloadFile(f"{fname}.slob")
		outputFilename = self.newTempFilePath(f"{fname}-2.epub")

		expectedFilename = self.downloadFile(f"{fname2}.epub")
		glos = Glossary()
		res = glos.convert(
			inputFilename=inputFilename,
			outputFilename=outputFilename,
			**convertArgs
		)
		self.assertEqual(outputFilename, res)

		def remove_toc_uid(data):
			return re.sub(
				b'<meta name="dtb:uid" content="[0-9a-f]{32}" />',
				b'<meta name="dtb:uid" content="" />',
				data,
			)

		def remove_content_uid(data):
			return re.sub(
				b'<dc:identifier id="uid" opf:scheme="uuid">[0-9a-f]{32}</dc:identifier>',
				b'<dc:identifier id="uid" opf:scheme="uuid"></dc:identifier>',
				data,
			)

		self.compareZipFiles(
			outputFilename,
			expectedFilename,
			{
				"OEBPS/toc.ncx": remove_toc_uid,
				"OEBPS/content.opf": remove_content_uid,
			},
		)

	def test_convert_slob_epub_1(self):
		self.convert_slob_epub(
			"100-en-fa-res",
			"100-en-fa-res-slob",
		)

	def test_convert_slob_epub_2(self):
		for sort in (True, False):
			self.convert_slob_epub(
				"100-en-fa-res",
				"100-en-fa-res-slob",
				sort=sort,
			)

	def test_convert_slob_epub_3(self):
		for sqlite in (True, False):
			self.convert_slob_epub(
				"100-en-fa-res",
				"100-en-fa-res-slob",
				sqlite=sqlite,
			)

	def test_convert_slob_epub_4(self):
		for direct in (True, False):
			self.convert_slob_epub(
				"100-en-fa-res",
				"100-en-fa-res-slob",
				direct=direct,
			)

if __name__ == "__main__":
	unittest.main()
