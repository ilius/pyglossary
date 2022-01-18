import sys
from os.path import dirname, abspath
import unittest

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from tests.glossary_test import TestGlossaryBase
from pyglossary.glossary import Glossary


class TestGlossaryStarDict(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update({
			"004-bar.sd/004-bar.dict": "9ea397f8",
			"004-bar.sd/004-bar.idx": "cf9440cf",
			"004-bar.sd/004-bar.ifo": "ada870e4",
			"004-bar.sd/004-bar.syn": "286b17bf",

			"100-en-de.sd/100-en-de.dict": "d74bf277",
			"100-en-de.sd/100-en-de.idx": "945b303c",
			"100-en-de.sd/100-en-de.ifo": "6529871f",

			"100-en-fa.sd/100-en-fa.dict": "223a0d1d",
			"100-en-fa.sd/100-en-fa.idx": "6df43378",
			"100-en-fa.sd/100-en-fa.ifo": "3f2086cd",
			"100-en-fa.sd/100-en-fa.syn": "1160fa0b",
			"100-en-fa-sd.txt": "85f9d3fc",

			"100-ja-en.sd/100-ja-en.dict": "39715f01",
			"100-ja-en.sd/100-ja-en.idx": "adf0e552",
			"100-ja-en.sd/100-ja-en.ifo": "b01e368c",
			"100-ja-en.sd/100-ja-en.syn": "76e6df95",

			"300-ru-en.txt": "77cfee2f",
			"300-ru-en.sd/300-ru-en.dict": "8be7fa4c",
			"300-ru-en.sd/300-ru-en.idx": "1cd30f1a",
			"300-ru-en.sd/300-ru-en.ifo": "0b135812",
			"300-ru-en.sd/300-ru-en.syn": "87ee3372",
		})

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

		glos = self.glos = Glossary()

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

	def convert_stardict_txt(
		self,
		inputFname: str,
		ouputFname: str,
		testId: str,
	):
		inputFilename = self.downloadFile(f"{inputFname}.sd/{inputFname}.ifo")
		outputFilename = self.newTempFilePath(
			f"{inputFname}-{testId}.txt"
		)
		expectedFilename = self.downloadFile(f"{ouputFname}.txt")
		glos = self.glos = Glossary()

		res = glos.convert(
			inputFilename=inputFilename,
			outputFilename=outputFilename,
		)
		self.assertEqual(outputFilename, res)

		self.compareTextFiles(outputFilename, expectedFilename)

	def test_convert_txt_stardict_0(self):
		self.convert_txt_stardict(
			"100-en-fa",
			config={"auto_sqlite": True},
			direct=True,
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

	def test_convert_txt_stardict_5(self):
		for sqlite in (None, False, True):
			self.convert_txt_stardict(
				"300-ru-en",
				syn=True,
				sqlite=sqlite,
			)

	def test_convert_txt_stardict_sqlite_no_alts(self):
		self.convert_txt_stardict(
			"100-en-fa",
			config={"enable_alts": False},
			sqlite=True,
		)

	def test_convert_stardict_txt_1(self):
		self.convert_stardict_txt(
			"100-en-fa",
			"100-en-fa-sd",
			"1",
		)


if __name__ == "__main__":
	unittest.main()
