import unittest
from os.path import join

from glossary_v2_test import TestGlossaryBase


class TestGlossaryBGL(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFile |= {
			"004-bar.txt.bgl",
			"100-en-fa.txt.bgl",
		}
		self.dataFileCRC32.update(
			{
				"Flavours_of_Malaysia.bgl": "46ef154b",
				"Flavours_of_Malaysia.txt_res/icon1.ico": "76a3b4c3",
				"Currency_In_Each_Country.bgl": "309f1b3f",
				"Solar_Physics_Glossary.bgl": "cc8f5ca1",
				"Farsi_Aviation_Dictionary.bgl": "efa7bee4",
			},
		)

	def convert_bgl_txt(
		self,
		fname,
		sha1sum=None,
		md5sum=None,
		resFiles=None,
		**convertArgs,
	):
		if resFiles is None:
			resFiles = {}
		resFilesPath = {
			resName: self.newTempFilePath(join(f"{fname}-2.txt_res", resName))
			for resName in resFiles
		}

		self.convert(
			f"{fname}.bgl",
			f"{fname}-2.txt",
			sha1sum=sha1sum,
			md5sum=md5sum,
			**convertArgs,
		)

		for resName in resFiles:
			resPathActual = resFilesPath[resName]
			resPathExpected = self.downloadFile(f"{fname}.txt_res/{resName}")
			self.compareBinaryFiles(resPathActual, resPathExpected)

	def test_convert_bgl_txt_1(self):
		self.convert_bgl_txt(
			"Flavours_of_Malaysia",
			sha1sum="2b1fae135df2aaaeac23fb1dde497a4b6a22fd95",
			resFiles=["icon1.ico"],
		)

	def test_convert_bgl_txt_2(self):
		self.convert_bgl_txt(
			"Currency_In_Each_Country",
			sha1sum="731147c72092d813dfe1ab35d420477478832443",
		)

	def test_convert_bgl_txt_3(self):
		self.convert_bgl_txt(
			"Solar_Physics_Glossary",
			sha1sum="f30b392c748c4c5bfa52bf7f9945c574617ff74a",
		)

	def test_convert_bgl_txt_4(self):
		self.convert_bgl_txt(
			"Farsi_Aviation_Dictionary",
			sha1sum="34729e2542085c6026090e9e3f49d10291393113",
			readOptions={
				"process_html_in_key": True,
			},
		)

	def test_convert_bgl_txt_5(self):
		self.convert_bgl_txt(
			"004-bar.txt",
			sha1sum="40525745c2f82241e72f2f39d073078459c30eb8",
		)

	def test_convert_bgl_txt_6(self):
		self.convert_bgl_txt(
			"100-en-fa.txt",
			sha1sum="3a479a6de968e25f8ba7ee717f8cfe94fdf0e3b0",
		)


if __name__ == "__main__":
	unittest.main()
