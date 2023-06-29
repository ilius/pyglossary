import sys
import typing
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from tests.glossary_v2_test import TestGlossaryBase


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

	def convert_dsl_txt(self: "typing.Self", fname, fname2, **convertArgs):
		self.convert(
			f"dsl/{fname}.dsl",
			f"{fname}-2.txt",
			compareText=f"dsl/{fname2}.txt",
			**convertArgs,
		)

	def test_convert_dsl_txt_1(self: "typing.Self"):
		self.convert_dsl_txt(
			"100-RussianAmericanEnglish-ru-en",
			"100-RussianAmericanEnglish-ru-en-v2",
		)

	def test_convert_dsl_txt_2(self: "typing.Self"):
		self.convert_dsl_txt(
			"001-empty-lines-br",
			"001-empty-lines-br",
		)

	def test_convert_dsl_txt_3(self: "typing.Self"):
		self.convert_dsl_txt(
			"002-m-tag_multiline-paragraph",
			"002-m-tag_multiline-paragraph",
		)

	def test_convert_dsl_txt_4(self: "typing.Self"):
		self.convert_dsl_txt(
			"003-ref-target-c",
			"003-ref-target-c",
		)




if __name__ == "__main__":
	unittest.main()
