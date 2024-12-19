import unittest

from glossary_v2_test import TestGlossaryBase


class TestGlossaryFreeDict(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update(
			{
				"100-en-de.tei": "542c210e",
				"100-en-de-v4.txt": "d420a669",
				"freedict-sample-2024-12-19.tei": "c33b89d5",
				"freedict-sample-2024-12-19.txt": "2a0a2235",
			},
		)

	def convert_tei_txt(self, fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.tei",
			f"{fname}-2.txt",
			compareText=f"{fname2}.txt",
			**convertArgs,
		)

	def test_convert_tei_txt_1(self):
		self.convert_tei_txt(
			"100-en-de",
			"100-en-de-v4",
			readOptions={"auto_comma": False},
		)
		self.convert_tei_txt(
			"100-en-de",
			"100-en-de-v4",
			readOptions={"auto_comma": True},
		)

	def test_convert_tei_txt_2(self):
		self.convert_tei_txt(
			"freedict-sample-2024-12-19",
			"freedict-sample-2024-12-19",
		)


if __name__ == "__main__":
	unittest.main()
