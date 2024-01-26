import unittest

from glossary_v2_test import TestGlossaryBase


class TestGlossaryDictionaryForMIDs(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)
		self.dataFileCRC32.update(
			{
				"100-en-fa.mids.zip": "32d1185f",
			},
		)

	def convert_txt_mids(self, fname, sha1sumDict, **convertArgs):
		outputFname = f"{fname}-2.mids.zip"
		outputFpath = self.newTempFilePath(outputFname)
		# expectedFpath = self.downloadFile(f"{fname}.mids.zip")
		self.convert(
			f"{fname}.txt",
			outputFname,
			**convertArgs,
		)
		self.checkZipFileSha1sum(outputFpath, sha1sumDict)

	def test_convert_txt_mids_1(self):
		sha1sumDict = {
			"DictionaryForMIDs.properties": "4260a87d6cdd55622dcfe395880bc913f96102b8",
			"directory1.csv": "1f1ab12b107608a1513254fff3c323bbcdfbd5cf",
			"index1.csv": "494268da410c520e56142b47610f6bbcfd53c79f",
			"searchlist.csv": "4f4513d1550436e867e1a79dbd073a7e5bb38e32",
		}
		self.convert_txt_mids("100-en-fa", sha1sumDict)


if __name__ == "__main__":
	unittest.main()
