import sys
from os.path import dirname, abspath, join
import unittest

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from tests.glossary_test import TestGlossaryBase
from pyglossary.glossary import Glossary


class TestGlossaryStarDict(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update({
			"Flavours_of_Malaysia.bgl": "46ef154b",
			"Flavours_of_Malaysia.txt": "e62d738f",
			"Flavours_of_Malaysia.txt_res/icon1.ico": "76a3b4c3",
		})

	def convert_bgl_txt(self, fname, fname2, resFiles, **convertArgs):
		inputFilename = self.downloadFile(f"{fname}.bgl")
		outputFname = f"{fname}-2.txt"
		outputFilename = self.newTempFilePath(outputFname)
		expectedFilename = self.downloadFile(f"{fname2}.txt")
		resFilesPath = {
			resName: self.newTempFilePath(join(f"{outputFname}_res", resName))
			for resName in resFiles
		}

		glos = self.glos = Glossary()
		res = glos.convert(
			inputFilename=inputFilename,
			outputFilename=outputFilename,
			**convertArgs
		)
		self.assertEqual(outputFilename, res)
		self.compareTextFiles(outputFilename, expectedFilename)
		for resName in resFiles:
			resPathActual = resFilesPath[resName]
			resPathExpected = self.downloadFile(f"{fname}.txt_res/{resName}")
			self.compareBinaryFiles(resPathActual, resPathExpected)

	def test_convert_bgl_txt_1(self):
		self.convert_bgl_txt(
			"Flavours_of_Malaysia",
			"Flavours_of_Malaysia",
			resFiles=["icon1.ico"],
		)


if __name__ == "__main__":
	unittest.main()
