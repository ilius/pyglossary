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
			"1-en-en-empty-ref.tei",
			"1-en-en-empty-ref.txt",
			"1-en-en-include-cycle.tei",
			"1-en-en-include-cycle.txt",
			"14-en-en.tei",
			"2-en-en-def-inline.tei",
			"2-en-en-def-inline.txt",
			"1-fr-en-example-note.tei",
			"1-fr-en-example-note.txt",
			"1-en-fa-p-lang.tei",
			"1-en-fa-p-lang.txt",
			"1-en-en-usg-nested.tei",
			"1-en-en-usg-nested.txt",
			"1-en-en-usg-whitespace.tei",
			"1-en-en-usg-whitespace.txt",
			"14-en-en-include.tei",
			"14-en-en-v2.txt",
			"freedict-sample-2024-12-19-v4.txt",
			"1-en-en-trans-cit-rerender.tei",
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
			"freedict-sample-2024-12-19-v4",
		)

	def test_convert_tei_txt_14_en_en(self):
		self.convert_tei_txt(
			"14-en-en",
			"14-en-en-v2",
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

	def test_convert_tei_txt_example_note(self):
		# <note> inside <cit type="example"> must not be dropped
		self.convert_tei_txt(
			"1-fr-en-example-note",
			"1-fr-en-example-note",
		)

	def test_convert_tei_txt_p_lang(self):
		# xml:lang on <p> must become lang, not a namespaced ns0:lang attribute
		self.convert_tei_txt(
			"1-en-fa-p-lang",
			"1-en-fa-p-lang",
		)

	def test_convert_tei_txt_usg_nested(self):
		# <usg> whose text is inside child elements (<lang>, <hi>) must be kept
		self.convert_tei_txt(
			"1-en-en-usg-nested",
			"1-en-en-usg-nested",
		)

	def test_convert_tei_txt_usg_whitespace(self):
		# line breaks and indentation inside <usg>/<lbl> must not leak into the tag
		self.convert_tei_txt(
			"1-en-en-usg-whitespace",
			"1-en-en-usg-whitespace",
		)

	def test_convert_tei_txt_empty_ref(self):
		# <ref/> without target or text must not produce bword://None
		self.convert_tei_txt(
			"1-en-en-empty-ref",
			"1-en-en-empty-ref",
		)

	def test_trans_cit_render_same_entry_twice(self):
		# Rendering the same entry element twice must give the same output,
		# and the source <cit> must be left unchanged: the grammar and note
		# children of a translation <cit> are copied, not moved out of the tree.
		from lxml import etree as ET

		tei = "{http://www.tei-c.org/ns/1.0}"
		inputFilename = self.downloadFile("1-en-en-trans-cit-rerender.tei")
		reader = Reader(Glossary())
		reader.open(inputFilename)
		try:
			with open(inputFilename, mode="rb") as file:
				context = ET.iterparse(file, events=("end",), tag=f"{tei}entry")
				_, entry = next(iter(context))
				cit = entry.find(f".//{tei}cit")
				citBefore = ET.tostring(cit)

				first = reader.getEntryByElem(entry).defi
				second = reader.getEntryByElem(entry).defi

				self.assertIn("interj", first)
				self.assertIn("a note", first)
				self.assertEqual(first, second)
				self.assertEqual(ET.tostring(cit), citBefore)
		finally:
			reader.close()

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
