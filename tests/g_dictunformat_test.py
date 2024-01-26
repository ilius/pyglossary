import unittest

from glossary_v2_test import TestGlossaryBase


class TestGlossaryDictunformat(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update(
			{
				"100-en-fa-2.dictunformat": "03a13c1a",
				"100-en-fa-2.dictunformat.txt": "c88207ec",
			},
		)

	def convert_dictunformat_txt(self, fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.dictunformat",
			f"{fname}-tmp.txt",
			compareText=f"{fname2}.txt",
			**convertArgs,
		)

	def test_convert_dictunformat_txt_1(self):
		self.convert_dictunformat_txt(
			"100-en-fa-2",
			"100-en-fa-2.dictunformat",
		)


if __name__ == "__main__":
	unittest.main()
