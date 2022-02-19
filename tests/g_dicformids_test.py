import sys
from os.path import dirname, abspath
import unittest

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from tests.glossary_test import TestGlossaryBase
from pyglossary.glossary import Glossary


class TestGlossaryDictionaryForMIDs(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)
		self.dataFileCRC32.update({
			"100-en-fa.mids.zip": "32d1185f",
		})

	def convert_txt_mids(self, fname, sha1sumDict, **convertArgs):
		outputFname = f"{fname}-2.mids.zip"
		outputFpath = self.newTempFilePath(outputFname)
		# expectedFpath = self.downloadFile(f"{fname}.mids.zip")
		self.convert(
			f"{fname}.txt",
			outputFname,
			**convertArgs
		)
		self.checkZipFileSha1sum(outputFpath, sha1sumDict)

	def test_convert_txt_mids_1(self):
		sha1sumDict = {
			"DictionaryForMIDs.properties": \
				"4260a87d6cdd55622dcfe395880bc913f96102b8",
			"directory1.csv": "70b0e683f2f4c9246500974a87467a3210d099c2",
			"index1.csv": "b941ad049e50b5c14b07383c590cc2d79520c365",
			"searchlist.csv": "d6f144dd001c7df79edb459fc9530515a747224d",
		}
		self.convert_txt_mids("100-en-fa", sha1sumDict)


if __name__ == "__main__":
	unittest.main()
