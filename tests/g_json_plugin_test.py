import sys
from os.path import dirname, abspath
import unittest

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.glossary_test import TestGlossaryBase
from pyglossary.glossary import Glossary


class TestGlossaryStarDict(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update({
			"004-bar.json": "7e4b2663",
			"100-en-de.json": "6fa8e159",
			"100-en-fa.json": "8d29c1be",
			"100-ja-en.json": "fab2c106",
		})

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

	def test_convert_txt_json_0(self):
		self.convert_txt_json("004-bar")

	def test_convert_txt_json_1(self):
		self.convert_txt_json("100-en-fa")

	def test_convert_txt_json_2(self):
		self.convert_txt_json("100-en-de")

	def test_convert_txt_json_3(self):
		self.convert_txt_json("100-ja-en")


if __name__ == "__main__":
	unittest.main()
