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
from pyglossary.core import tmpDir, cacheDir
from pyglossary.os_utils import rmtree

Glossary.init()


dataURL = "https://raw.githubusercontent.com/ilius/pyglossary-test/main/{filename}"

dataDir = join(cacheDir, "test")

dataFileSize = {
	"100-en-fa.txt": 29885,
	"100-en-fa.csv": 30923,
	"100-en-fa.sd/100-en-fa.dict": 28571,
	"100-en-fa.sd/100-en-fa.idx": 1557,
	"100-en-fa.sd/100-en-fa.ifo": 348,
	"100-en-fa.sd/100-en-fa.syn": 76,

	"100-en-de.txt": 15117,
	"100-en-de.csv": 15970,
	"100-en-de.sd/100-en-de.dict": 13601,
	"100-en-de.sd/100-en-de.idx": 1323,
	"100-en-de.sd/100-en-de.ifo": 864,

	"100-ja-en.txt": 31199,
	"100-ja-en.csv": 32272,
	"100-ja-en.sd/100-ja-en.dict": 27585,
	"100-ja-en.sd/100-ja-en.idx": 2014,
	"100-ja-en.sd/100-ja-en.ifo": 845,
	"100-ja-en.sd/100-ja-en.syn": 1953,

	"004-bar.txt": 45,
	"004-bar.sd/004-bar.dict": 16,
	"004-bar.sd/004-bar.idx": 45,
	"004-bar.sd/004-bar.ifo": 134,
	"004-bar.sd/004-bar.syn": 24,
}



class TestGlossary(unittest.TestCase):
	def __init__(self, *args, **kwargs):
		unittest.TestCase.__init__(self, *args, **kwargs)
		self.maxDiff = None
		self._cleanupPathList = set()

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
		size = dataFileSize[filename]
		fpath = join(dataDir, filename.replace("/", "__"))
		if isfile(fpath):
			if os.stat(fpath).st_size != size:
				raise RuntimeError(f"Invalid file size for: {fpath}")
			return fpath
		try:
			with urlopen(dataURL.format(filename=filename)) as res:
				data = res.read()
		except Exception as e:
			e.msg += f", filename={filename}"
			raise e
		if len(data) != size:
			raise RuntimeError(f"Invalid file size for: {fpath}")
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
		self.assertTrue(isfile(fpath1))
		self.assertTrue(isfile(fpath2))
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

	def test_convert_txt_csv_1(self):
		self.convert_txt_csv("100-en-fa")

	def test_convert_txt_csv_2(self):
		self.convert_txt_csv("100-en-de")

	def test_convert_txt_csv_3(self):
		self.convert_txt_csv("100-ja-en")

	def convert_txt_stardict(
		self,
		fname,
		syn=True,
		dictzip=False,
		config=None,
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
		for sqlite in (False, True):
			self.convert_txt_stardict(
				"100-en-fa",
				sqlite=sqlite,
			)

	def test_convert_txt_stardict_2(self):
		for sqlite in (False, True):
			self.convert_txt_stardict(
				"004-bar",
				sqlite=sqlite,
			)

	def test_convert_txt_stardict_3(self):
		for sqlite in (False, True):
			self.convert_txt_stardict(
				"100-en-de",
				syn=False,
				sqlite=sqlite,
			)

	def test_convert_txt_stardict_4(self):
		for sqlite in (False, True):
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


if __name__ == "__main__":
	unittest.main()
