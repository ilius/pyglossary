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
			"100-RussianAmericanEnglish-ru-en.dsl": "c24491e0",
			"100-RussianAmericanEnglish-ru-en-v4.txt": "5db01289",
		})

	def convert_dsl_txt(self: "typing.Self", fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.dsl",
			f"{fname}-2.txt",
			compareText=f"{fname2}.txt",
			**convertArgs,
		)

	def test_convert_dsl_txt_1(self: "typing.Self"):
		self.convert_dsl_txt(
			"100-RussianAmericanEnglish-ru-en",
			"100-RussianAmericanEnglish-ru-en-v4",
		)


if __name__ == "__main__":
	unittest.main()
