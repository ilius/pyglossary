import sys
import typing
import unittest
import tempfile
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from tests.glossary_v2_test import TestGlossaryBase
from pyglossary.glossary_v2 import ConvertArgs, Glossary


class TestGlossaryDSL(TestGlossaryBase):
	def __init__(self: "typing.Self", *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update({
			"dsl/100-RussianAmericanEnglish-ru-en.dsl": "c24491e0",
			"dsl/100-RussianAmericanEnglish-ru-en-v2.txt": "258050fb",
			"dsl/001-empty-lines-br.dsl": "6f2fca1a",
			"dsl/001-empty-lines-br.txt": "74e578ff",
			"dsl/002-m-tag_multiline-paragraph.dsl": "c7b924f5",
			"dsl/002-m-tag_multiline-paragraph.txt": "427f8a5d",
			"dsl/003-ref-target-c.dsl": "9c1396c4",
			"dsl/003-ref-target-c.txt": "ab41cedf",
		})

	def convert_string_dsl_txt(
		self: "typing.Self",
		dsl: str,
		txtExpected: str,
		removeInfo: bool = True,
		**convertArgs,
	):
		dsl_fname = tempfile.mktemp(suffix=".dsl")
		txt_fname = tempfile.mktemp(suffix=".txt")
		with open(dsl_fname, "wt", encoding="utf-8") as _file:
			_file.write(dsl)

		glos = self.glos = Glossary()
		# glos.config = config
		res = glos.convert(ConvertArgs(
			inputFilename=dsl_fname,
			outputFilename=txt_fname,
			**convertArgs,
		))
		self.assertEqual(txt_fname, res)

		with open(txt_fname, "rt", encoding="utf-8") as _file:
			txtActual = _file.read()

		if removeInfo:
			txtActual = "\n".join([
				line
				for line in txtActual.split("\n")
				if line and not line.startswith("#")
			])

		self.assertEqual(txtExpected, txtActual)

	def convert_dsl_txt(self: "typing.Self", fname, fname2, **convertArgs):
		self.convert(
			f"dsl/{fname}.dsl",
			f"{fname}-2.txt",
			compareText=f"dsl/{fname2}.txt",
			**convertArgs,
		)

	def test_russianAmericanEnglish(self: "typing.Self"):
		self.convert_dsl_txt(
			"100-RussianAmericanEnglish-ru-en",
			"100-RussianAmericanEnglish-ru-en-v2",
		)

	def test_empty_lines_br(self: "typing.Self"):
		self.convert_dsl_txt(
			"001-empty-lines-br",
			"001-empty-lines-br",
		)

	def test_m_tag_multiline_paragraph(self: "typing.Self"):
		self.convert_dsl_txt(
			"002-m-tag_multiline-paragraph",
			"002-m-tag_multiline-paragraph",
		)

	def test_ref_target_c(self: "typing.Self"):
		self.convert_dsl_txt(
			"003-ref-target-c",
			"003-ref-target-c",
		)

	def test_bashkir_basque_headword_formatting(self: "typing.Self"):
		# from Bashkir -> Basque dict (001-headword-with-formatting.dsl)
		dsl = (
			"{[c slategray]}{to }{[/c]}tell {[c slategray]}smb{[/c]} how to do "
			"{[c slategray]}smth{[/c]}\n    [m1][trn]"
			"рассказать кому-либо, как что-либо делать[/trn][/m]"
		)
		txt = (
			"tell smb how to do smth\t"
			'<p style="padding-left:1em;margin:0">'
			"рассказать кому-либо, как что-либо делать</p>"
		)
		self.convert_string_dsl_txt(dsl, txt)

	def test_headword_paran(self: "typing.Self"):
		self.convert_string_dsl_txt(
			"headword with (parenthesis)\n    test",
			'headword with (parenthesis)|headword with\ttest',
		)

	def test_headword_paran_2(self: "typing.Self"):
		self.convert_string_dsl_txt(
			"(headword with) parenthesis\n    test",
			'(headword with) parenthesis|parenthesis\ttest',
		)

	def test_headword_paran_escaped(self: "typing.Self"):
		self.convert_string_dsl_txt(
			"headword \\(with escaped parenthesis\\)\n    test",
			'headword (with escaped parenthesis)\ttest',
		)

	def test_headword_paran_escaped_2(self: "typing.Self"):
		self.convert_string_dsl_txt(
			"headword (with escaped right \\) parenthesis)\n    test",
			'headword (with escaped right \\\\) parenthesis)|headword\ttest',
		)

	def test_headword_curly(self: "typing.Self"):
		self.convert_string_dsl_txt(
			"headword with {[b]}curly brackets{[/b]}\n    test",
			'headword with curly brackets\ttest',
		)

	def test_headword_curly_escaped(self: "typing.Self"):
		self.convert_string_dsl_txt(
			"headword with escaped \\{\\}curly brackets\\{\n    test",
			'headword with escaped {}curly brackets{\ttest',
		)



if __name__ == "__main__":
	unittest.main()
