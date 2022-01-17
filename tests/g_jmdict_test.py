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
			"050-JMdict-English": "aec9ad8c",
			"050-JMdict-English.txt": "edd13a27",
		})

	def convert_jmdict_txt(self, fname, fname2, **convertArgs):
		inputFilename = self.downloadFile(fname)
		outputFilename = self.newTempFilePath(f"{fname}-2.txt")
		expectedFilename = self.downloadFile(f"{fname2}.txt")
		glos = Glossary()
		res = glos.convert(
			inputFilename=inputFilename,
			outputFilename=outputFilename,
			inputFormat="JMDict",
			**convertArgs
		)
		self.assertEqual(outputFilename, res)
		self.compareTextFiles(outputFilename, expectedFilename)

	def test_convert_jmdict_txt_1(self):
		self.convert_jmdict_txt(
			"050-JMdict-English",
			"050-JMdict-English",
		)


if __name__ == "__main__":
	unittest.main()
