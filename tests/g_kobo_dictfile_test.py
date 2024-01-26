import unittest

import mistune  # noqa: F401, to ensure it's installed
from glossary_v2_test import TestGlossaryBase


class TestGlossaryDictfile(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update(
			{
				"022-en-en.df": "edff6de1",
				"022-en-en.df.txt": "93a2450f",
				"022-en-en.df.txt.df": "8e952e56",
				"res/01cf5b41.gif": "01cf5b41",
				"res/1f3c1a36.gif": "1f3c1a36",
				"res/3af9fd5d.gif": "3af9fd5d",
				"res/6684158d.gif": "6684158d",
			},
		)

	def convert_df_txt(self, fname, fname2, resFiles, **convertArgs):
		resFilesPath = {
			resFileName: self.newTempFilePath(f"{fname}-2.txt_res/{resFileName}")
			for resFileName in resFiles
		}

		self.convert(
			f"{fname}.df",
			f"{fname}-2.txt",
			compareText=f"{fname2}.txt",
			**convertArgs,
		)

		for resFileName in resFiles:
			fpath1 = self.downloadFile(f"res/{resFileName}")
			fpath2 = resFilesPath[resFileName]
			self.compareBinaryFiles(fpath1, fpath2)

	def convert_txt_df(self, fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.txt",
			f"{fname}-2.df",
			compareText=f"{fname2}.df",
			**convertArgs,
		)

	def test_convert_df_txt_1(self):
		self.convert_df_txt(
			"022-en-en",
			"022-en-en.df",
			resFiles=[
				"01cf5b41.gif",
				"1f3c1a36.gif",
				"3af9fd5d.gif",
				"6684158d.gif",
			],
		)

	def test_convert_txt_df_1(self):
		self.convert_txt_df(
			"022-en-en.df",
			"022-en-en.df.txt",
		)


if __name__ == "__main__":
	unittest.main()
