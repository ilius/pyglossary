import os
import unittest

from glossary_v2_test import Glossary, TestGlossaryBase

from pyglossary.plugins.freedict.reader import Reader


class TestGlossaryFreeDict(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFile |= {
			"1-en-de-labels.tei",
			"100-en-de-v6.txt",
			"1-en-de-labels.txt",
			"1-en-en-comment.tei",
			"1-en-en-comment.txt",
			"1-en-en-include-cycle.tei",
			"1-en-en-include-cycle.txt",
			"14-en-en.tei",
			"2-en-en-def-inline.tei",
			"2-en-en-def-inline.txt",
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

	def test_convert_tei_txt_comments(self):
		# XML comments inside <gramGrp> and <sense> must be skipped
		self.convert_tei_txt(
			"1-en-en-comment",
			"1-en-en-comment",
		)

	def test_convert_tei_txt_include_cycle(self):
		# a file that XIncludes itself must not recurse forever
		self.convert_tei_txt(
			"1-en-en-include-cycle",
			"1-en-en-include-cycle",
		)

	def test_convert_tei_txt_def_inline(self):
		# inline markup inside <def> keeps its spacing, without separators
		self.convert_tei_txt(
			"2-en-en-def-inline",
			"2-en-en-def-inline",
		)

	def test_input_file_size_top_level_only(self):
		# 14-en-en.tei XIncludes 14-en-en-include.tei; the included file
		# must not overwrite input_file_size of the top-level file
		# (Glossary.convert() clears glossary info when writing, so read directly)
		inputFilename = self.downloadFile("14-en-en.tei")
		glos = Glossary()
		reader = Reader(glos)
		reader.open(inputFilename)
		try:
			# includes are opened while iterating
			for _ in reader:
				pass
			self.assertEqual(
				glos.getInfo("input_file_size"),
				str(os.path.getsize(inputFilename)),
			)
		finally:
			reader.close()


if __name__ == "__main__":
	unittest.main()
