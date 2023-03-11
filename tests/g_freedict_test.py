import sys
import typing
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from tests.glossary_v2_test import TestGlossaryBase


class TestGlossaryFreeDict(TestGlossaryBase):
	def __init__(self: "typing.Self", *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update({
			"100-en-de.tei": "542c210e",
		})

	def convert_tei_txt(self: "typing.Self", fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.tei",
			f"{fname}-2.txt",
			compareText=f"{fname2}.txt",
			**convertArgs,
		)

	def test_convert_tei_txt_1(self: "typing.Self"):
		self.convert_tei_txt(
			"100-en-de",
			"100-en-de-v2",
			infoOverride={"input_file_size": None},
		)


if __name__ == "__main__":
	unittest.main()
