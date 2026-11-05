import unittest

from glossary_v2_test import TestGlossaryBase


class TestGlossaryFreeDict(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFile |= {
			"1-en-de-labels.tei",
			"100-en-de-v6.txt",
			"1-en-de-labels.txt",
			"14-en-en.tei",
			"14-en-en-include.tei",
			"14-en-en.txt",
			"freedict-sample-2024-12-19-v3.txt",
		}
		self.dataFileCRC32 |= {
			"100-en-de.tei": "542c210e",
			"freedict-sample-2024-12-19.tei": "c33b89d5",
		}

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
			"100-en-de-v6",
			readOptions={"auto_comma": False},
		)
		self.convert_tei_txt(
			"100-en-de",
			"100-en-de-v6",
			readOptions={"auto_comma": True},
		)

	def test_convert_tei_txt_2(self):
		self.convert_tei_txt(
			"freedict-sample-2024-12-19",
			"freedict-sample-2024-12-19-v3",
		)

	def test_convert_tei_txt_14_en_en(self):
		self.convert_tei_txt(
			"14-en-en",
			"14-en-en",
			readOptions={"auto_comma": True},
		)

	def test_convert_tei_txt_labels(self):
		self.convert_tei_txt(
			"1-en-de-labels",
			"1-en-de-labels",
		)


if __name__ == "__main__":
	unittest.main()
