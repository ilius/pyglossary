import sys
from os.path import dirname, abspath
import unittest

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from tests.glossary_test import TestGlossaryBase
from pyglossary.glossary import Glossary
from pyglossary.entry import Entry


class TestGlossaryStarDict(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update({
			"100-en-fa-res.slob": "0216d006",
			"100-en-fa-res-slob.txt": "c73100b3",
			"100-en-fa-res-slob-sort.txt": "8253fe96",
		})

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


if __name__ == "__main__":
	unittest.main()
