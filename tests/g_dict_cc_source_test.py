import unittest

from glossary_v2_test import TestGlossaryBase


class TestGlossaryDictCcSource(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFile |= {
			"29-en-de.txt",
			"29-en-de.tsv",
			"29-en-de-source-de.tsv",
		}

	def convert_dict_cc_source(self, fname, fname2, source_lang, **convertArgs):
		self.convert(
			f"{fname}.txt",
			f"{fname}-2.tsv",
			compareText=f"{fname2}.tsv",
			inputFormat="Dictcc_source",
			readOptions={
				"source_lang": source_lang,
			},
			**convertArgs,
		)

	def test_convert_dict_cc_source_en(self):
		self.convert_dict_cc_source(
			"29-en-de",
			"29-en-de",
			"en",
		)

	def test_convert_dict_cc_source_de(self):
		self.convert_dict_cc_source(
			"29-en-de",
			"29-en-de-source-de",
			"de",
		)

	def test_source_lang_required(self):
		with self.assertRaises(ValueError):
			self.convert_dict_cc_source(
				"29-en-de",
				"29-en-de",
				"",
				name="no-lang.txt",
			)

	def test_source_lang_not_in_file(self):
		with self.assertRaises(ValueError):
			self.convert_dict_cc_source(
				"29-en-de",
				"29-en-de",
				"fr",
			)


if __name__ == "__main__":
	unittest.main()
