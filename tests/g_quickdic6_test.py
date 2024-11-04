import os
import unittest

from glossary_v2_test import TestGlossaryBase


class TestGlossaryQuickDic6(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update(
			{
				"100-en-de-v4.txt": "d420a669",
				"100-en-de-v4.txt.quickdic": "9d4ccc13",
				"100-en-de-v4.txt.quickdic.txt": "2dc4fc17",
				"100-en-fa.txt.quickdic": "2bd483df",
				"100-en-fa.txt.quickdic.txt": "50994fb5",
			},
		)

		os.environ["QUICKDIC_CREATION_TIME"] = "1730579400"

	def convert_txt_quickdic(self, fname, sha1sum, **convertArgs):
		self.convert(
			f"{fname}.txt",
			f"{fname}-2.quickdic",
			sha1sum=sha1sum,
			**convertArgs,
		)

	def convert_quickdic_txt(self, fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.quickdic",
			f"{fname}-2.txt",
			compareText=f"{fname2}.txt",
			**convertArgs,
		)

	def test_convert_txt_quickdic_1(self):
		self.convert_txt_quickdic(
			"100-en-de-v4",
			"c8d9694624bace08e6e999db75c9156776f257c9",
		)

	def test_convert_quickdic_txt_1(self):
		self.convert_quickdic_txt(
			"100-en-de-v4.txt",
			"100-en-de-v4.txt.quickdic",
		)

	def test_convert_txt_quickdic_2(self):
		self.convert_txt_quickdic(
			"100-en-fa",
			"371ac30d5ddedffe0a1c54b8a050aef62e5b91a5",
		)

	def test_convert_quickdic_txt_2(self):
		self.convert_quickdic_txt(
			"100-en-fa.txt",
			"100-en-fa.txt.quickdic",
		)


if __name__ == "__main__":
	unittest.main()
