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
			"100-en-de.csv": "b5283518",
			"100-en-fa.csv": "eb8b0474",
			"100-ja-en.csv": "7af18cf3",
		})

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


if __name__ == "__main__":
	unittest.main()
