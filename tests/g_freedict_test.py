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
			"100-en-de.tei": "542c210e",
		})

	def convert_tei_txt(self, fname, fname2, **convertArgs):
		inputFilename = self.downloadFile(f"{fname}.tei")
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

	def test_convert_tei_txt_1(self):
		self.convert_tei_txt(
			"100-en-de",
			"100-en-de-v2",
			infoOverride={"input_file_size": None},
		)

