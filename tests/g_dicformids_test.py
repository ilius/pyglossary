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

	def convert_txt_mids(self, fname, fname2, **convertArgs):
		outputFname = f"{fname}-2.mids.zip"
		outputFpath = self.newTempFilePath(outputFname)
		# expectedFpath = self.downloadFile(f"{fname}.mids.zip")
		self.convert(
			f"{fname}.txt",
			outputFname,
			**convertArgs
		)
		sha1sumDict = {
			"DictionaryForMIDs.properties": \
				"4260a87d6cdd55622dcfe395880bc913f96102b8",
			"directory1.csv": "70b0e683f2f4c9246500974a87467a3210d099c2",
			"index1.csv": "5033902993e44257fce29df8443481958a101602",
			"searchlist.csv": "d6f144dd001c7df79edb459fc9530515a747224d",
		}
		self.checkZipFileSha1sum(outputFpath, sha1sumDict)
