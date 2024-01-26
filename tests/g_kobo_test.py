import gzip
import unittest

import marisa_trie  # noqa: F401, to ensure it's installed
from glossary_v2_test import TestGlossaryBase


class TestGlossaryKobo(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)
		# self.dataFileCRC32.update({})

	def convert_txt_kobo(self, fname, sha1sumDict, **convertArgs):
		outputFname = f"{fname}-2.kobo.zip"
		outputFpath = self.newTempFilePath(outputFname)
		# expectedFpath = self.downloadFile(f"{fname}.kobo.zip")
		self.convert(
			f"{fname}.txt",
			outputFname,
			**convertArgs,
		)
		dataReplaceFuncs = {
			_zfname: gzip.decompress for _zfname in sha1sumDict if _zfname != "words"
		}
		self.checkZipFileSha1sum(
			outputFpath,
			sha1sumDict=sha1sumDict,
			dataReplaceFuncs=dataReplaceFuncs,
		)

	def test_convert_txt_kobo_1(self):
		sha1sumDict = {
			"11.html": "39f0f46560da7398ab0d3b19cc1c2387ecd201dd",
			"aa.html": "df9460450e8b46e913c57bf39dcc799ffdc2fb33",
			"ab.html": "be4271a8508dbb499bafd439810af621a7b3474f",
			"words": "d0f74e854f090fbaa8211bcfd162ad99ec4da0a3",
		}
		self.convert_txt_kobo("100-en-fa", sha1sumDict)


if __name__ == "__main__":
	unittest.main()
