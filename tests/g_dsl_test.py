import sys
import tempfile
import unittest
from os.path import abspath, dirname, join

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from glossary_v2_test import TestGlossaryBase

from pyglossary.glossary_v2 import ConvertArgs, Glossary


class TestGlossaryDSL(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update(
			{
				"dsl/100-RussianAmericanEnglish-ru-en.dsl": "c24491e0",
				"dsl/100-RussianAmericanEnglish-ru-en-v3.txt": "43b6d58e",
				"dsl/001-empty-lines-br.dsl": "6f2fca1a",
				"dsl/001-empty-lines-br.txt": "74e578ff",
				"dsl/002-m-tag_multiline-paragraph.dsl": "334079e3",
				"dsl/002-m-tag_multiline-paragraph-v2.txt": "d5001afd",
				"dsl/003-ref-target-c.dsl": "9c1396c4",
				"dsl/003-ref-target-c.txt": "ab41cedf",
			},
		)

	def convert_string_dsl_txt(
		self,
		dsl: str,
		txtExpected: str,
		removeInfo: bool = True,
		**convertArgs,
	):
		prefix = join(self.tempDir, "")
		dsl_fname = tempfile.mktemp(suffix=".dsl", prefix=prefix)
		txt_fname = tempfile.mktemp(suffix=".txt", prefix=prefix)
		with open(dsl_fname, "w", encoding="utf-8") as _file:
			_file.write(dsl)

		glos = self.glos = Glossary()
		# glos.config = config
		res = glos.convert(
			ConvertArgs(
				inputFilename=dsl_fname,
				outputFilename=txt_fname,
				**convertArgs,
			),
		)
		self.assertEqual(txt_fname, res)

		with open(txt_fname, encoding="utf-8") as _file:
			txtActual = _file.read()

		if removeInfo:
			txtActual = "\n".join(
				[
					line
					for line in txtActual.split("\n")
					if line and not line.startswith("#")
				],
			)

		self.assertEqual(txtExpected, txtActual)

	def convert_dsl_txt(self, fname, fname2, **convertArgs):
		self.convert(
			f"dsl/{fname}.dsl",
			f"{fname}-2.txt",
			compareText=f"dsl/{fname2}.txt",
			**convertArgs,
		)

	def test_russianAmericanEnglish(self):
		self.convert_dsl_txt(
			"100-RussianAmericanEnglish-ru-en",
			"100-RussianAmericanEnglish-ru-en-v3",
		)

	def test_empty_lines_br(self):
		self.convert_dsl_txt(
			"001-empty-lines-br",
			"001-empty-lines-br",
		)

	def test_m_tag_multiline_paragraph(self):
		self.convert_dsl_txt(
			"002-m-tag_multiline-paragraph",
			"002-m-tag_multiline-paragraph-v2",
		)

	def test_ref_target_c(self):
		self.convert_dsl_txt(
			"003-ref-target-c",
			"003-ref-target-c",
		)

	def test_headword_formatting_bashkir_basque(self):
		# from Bashkir -> Basque dict (001-headword-with-formatting.dsl)
		dsl = (
			"{[c slategray]}{to }{[/c]}tell "
			"{[c slategray]}smb{[/c]} how to do "
			"{[c slategray]}smth{[/c]}\n    [m1][trn]"
			"рассказать кому-либо, как что-либо делать[/trn][/m]"
		)
		txt = (
			"tell smb how to do smth\t"
			'<b><font color="slategray">to </font>tell '
			'<font color="slategray">smb</font> how to do '
			'<font color="slategray">smth</font></b><br/>'
			'<p style="padding-left:1em;margin:0">'
			"рассказать кому-либо, как что-либо делать</p>"
		)
		self.convert_string_dsl_txt(dsl, txt)

	def test_headword_formatting_english(self):
		dsl = (
			"{[c slategray]}{to }{[/c]}tell"
			" {[c violet]}smb{[/c]} {[u]}how{[/u]}"
			" to do {[c violet]}smth{[/c]} {[sub]subscript[/sub]}\n"
			"   [m1]1. main meaning[/m]\n"
			"   [m2]a. first submeaning[/m]\n"
			"   [m2]b. second submeaning[/m]\n"
		)
		txt = (
			"tell smb how to do smth\t"
			'<b><font color="slategray">to </font>tell'
			' <font color="violet">smb</font> <u>how</u>'
			' to do <font color="violet">smth</font> <sub>subscript</sub></b><br/>'
			'<p style="padding-left:1em;margin:0">1. main meaning</p>'
			'<p style="padding-left:2em;margin:0">a. first submeaning</p>'
			'<p style="padding-left:2em;margin:0">b. second submeaning</p>'
		)
		self.convert_string_dsl_txt(dsl, txt)

	def test_headword_paran(self):
		self.convert_string_dsl_txt(
			"headword with (parenthesis)\n    test",
			"headword with parenthesis|headword with\ttest",
		)

	def test_headword_paran_2(self):
		self.convert_string_dsl_txt(
			"(headword with) parenthesis\n    test",
			"headword with parenthesis|parenthesis\ttest",
		)

	def test_headword_paran_escaped(self):
		self.convert_string_dsl_txt(
			"headword \\(with escaped parenthesis\\)\n    test",
			"headword (with escaped parenthesis)\ttest",
		)

	def test_headword_paran_escaped_2(self):
		self.convert_string_dsl_txt(
			"headword (with escaped right \\) parenthesis)\n    test",
			"headword with escaped right \\\\) parenthesis|headword\ttest",
		)

	def test_headword_curly(self):
		txt = (
			"headword with curly brackets\t"
			"<b>headword with <b>curly brackets</b></b><br/>test"
		)
		self.convert_string_dsl_txt(
			"headword with {[b]}curly brackets{[/b]}\n    test",
			txt,
		)

	def test_headword_curly_escaped(self):
		self.convert_string_dsl_txt(
			"headword with escaped \\{\\}curly brackets\\{\n    test",
			"headword with escaped {}curly brackets{\ttest",
		)

	def test_double_brackets_1(self):
		self.convert_string_dsl_txt(
			"test\n    hello [[world]]",
			"test\thello [world]",
		)

	def test_double_brackets_2(self):
		self.convert_string_dsl_txt(
			"test\n    hello [[",
			"test\thello [",
		)

	def test_double_brackets_3(self):
		self.convert_string_dsl_txt(
			"test\n    hello ]]",
			"test\thello ]",
		)

	def test_ref_double_ltgt(self):
		self.convert_string_dsl_txt(
			"test\n    hello <<world>>",
			'test\thello <a href="bword://world">world</a>',
		)

	def test_ref_double_ltgt_escaped(self):
		self.convert_string_dsl_txt(
			"test\n    hello \\<<world\\>>",
			"test\thello &lt;&lt;world&gt;&gt;",
		)


if __name__ == "__main__":
	unittest.main()
