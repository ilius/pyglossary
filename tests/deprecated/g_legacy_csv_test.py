import sys
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from glossary_v2_test import TestGlossaryBase

from pyglossary.glossary import Glossary as GlossaryLegacy


class TestLegacyGlossaryCSV(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update(
			{
				"100-en-de-v4.csv": "2890fb3e",
				"100-en-fa.csv": "eb8b0474",
				"100-en-fa-semicolon.csv": "b3f04599",
				"100-ja-en.csv": "7af18cf3",
			},
		)

	def convert_csv_txt_rw(self, fname, fname2, infoOverride=None):
		inputFilename = self.downloadFile(f"{fname}.csv")
		outputFilename = self.newTempFilePath(f"{fname}-2.txt")
		expectedFilename = self.downloadFile(f"{fname2}.txt")
		glos = self.glos = GlossaryLegacy()
		# using glos.convert will add "input_file_size" info key
		# perhaps add another optional argument to glos.convert named infoOverride

		rRes = glos.read(inputFilename, direct=True)
		self.assertTrue(rRes)

		if infoOverride:
			for key, value in infoOverride.items():
				glos.setInfo(key, value)

		wRes = glos.write(outputFilename, format="Tabfile")
		self.assertEqual(outputFilename, wRes)

		self.compareTextFiles(outputFilename, expectedFilename)
		glos.cleanup()

	def test_convert_csv_txt_4(self):
		self.convert_csv_txt_rw(
			"100-en-fa",
			"100-en-fa",
			infoOverride={"input_file_size": None},
		)


if __name__ == "__main__":
	unittest.main()
