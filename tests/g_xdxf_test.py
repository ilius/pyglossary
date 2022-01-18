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
			"100-cyber_lexicon_en-es.txt": "8571e444",
			"100-cyber_lexicon_en-es.xdxf": "8d9ba394"
		})

	def convert_xdxf_txt(self, fname, fname2, **convertArgs):
		inputFilename = self.downloadFile(f"{fname}.xdxf")
		outputFilename = self.newTempFilePath(f"{fname}-2.txt")
		expectedFilename = self.downloadFile(f"{fname2}.txt")
		glos = self.glos = Glossary()
		res = glos.convert(
			inputFilename=inputFilename,
			outputFilename=outputFilename,
			**convertArgs
		)
		self.assertEqual(outputFilename, res)
		self.compareTextFiles(outputFilename, expectedFilename)

	def test_convert_xdxf_txt_1(self):
		self.convert_xdxf_txt(
			"100-cyber_lexicon_en-es",
			"100-cyber_lexicon_en-es",
		)


if __name__ == "__main__":
	unittest.main()
