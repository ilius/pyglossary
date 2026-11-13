import unittest

from glossary_v2_test import Glossary, TestGlossaryBase

from pyglossary.plugins.freedict_md.reader import Reader


class TestGlossaryFreeDictMarkdown(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFile |= {
			"1-en-de-labels.tei",
			"1-en-de-labels-md.txt",
			"1-en-en-comment.tei",
			"1-en-en-comment-md.txt",
			"1-en-en-empty-ref.tei",
			"1-en-en-empty-ref-md.txt",
			"1-en-en-include-cycle.tei",
			"1-en-en-include-cycle-md.txt",
			"1-en-en-trans-cit-rerender.tei",
			"1-en-en-usg-nested.tei",
			"1-en-en-usg-nested-md.txt",
			"1-en-en-usg-whitespace.tei",
			"1-en-en-usg-whitespace-md.txt",
			"1-en-fa-p-lang.tei",
			"1-en-fa-p-lang-md.txt",
			"1-fr-en-example-note.tei",
			"1-fr-en-example-note-md.txt",
			"2-en-en-def-inline.tei",
			"2-en-en-def-inline-md.txt",
			"14-en-en.tei",
			"14-en-en-md.txt",
		}

	def convert_tei_txt(self, fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.tei",
			f"{fname}-2.txt",
			compareText=f"{fname2}.txt",
			inputFormat="FreeDictMarkdown",
			**convertArgs,
		)

	def test_convert_tei_txt_labels(self):
		# <usg> and <lbl> render as tags, including nested markup
		self.convert_tei_txt("1-en-de-labels", "1-en-de-labels-md")

	def test_convert_tei_txt_comments(self):
		# XML comments inside <gramGrp> and <sense> must be skipped
		self.convert_tei_txt("1-en-en-comment", "1-en-en-comment-md")

	def test_convert_tei_txt_empty_ref(self):
		# <ref/> without target or text must not produce bword://None
		self.convert_tei_txt("1-en-en-empty-ref", "1-en-en-empty-ref-md")

	def test_convert_tei_txt_include_cycle(self):
		# a file that XIncludes itself must not recurse forever
		self.convert_tei_txt(
			"1-en-en-include-cycle",
			"1-en-en-include-cycle-md",
		)

	def test_convert_tei_txt_usg_nested(self):
		# <usg> whose text is inside child elements (<lang>, <hi>) must be kept
		self.convert_tei_txt("1-en-en-usg-nested", "1-en-en-usg-nested-md")

	def test_convert_tei_txt_usg_whitespace(self):
		# line breaks and indentation inside <usg>/<lbl> must not leak into the tag
		self.convert_tei_txt(
			"1-en-en-usg-whitespace",
			"1-en-en-usg-whitespace-md",
		)

	def test_convert_tei_txt_p_lang(self):
		# xml:lang on <p> must become lang, not a namespaced ns0:lang attribute
		self.convert_tei_txt("1-en-fa-p-lang", "1-en-fa-p-lang-md")

	def test_convert_tei_txt_example_note(self):
		# <note> inside <cit type="example"> must not be dropped
		self.convert_tei_txt("1-fr-en-example-note", "1-fr-en-example-note-md")

	def test_convert_tei_txt_def_inline(self):
		# inline markup inside <def> keeps its spacing, without separators
		self.convert_tei_txt("2-en-en-def-inline", "2-en-en-def-inline-md")

	def test_convert_tei_txt_14_en_en(self):
		self.convert_tei_txt("14-en-en", "14-en-en-md")

	def test_trans_cit_render_same_entry_twice(self):
		# Rendering the same entry element twice must give the same output,
		# and the source <cit> must be left unchanged.
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


if __name__ == "__main__":
	unittest.main()
