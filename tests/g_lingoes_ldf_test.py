import sys
import typing
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from tests.glossary_v2_test import TestGlossaryBase


class TestGlossaryLingoesLDF(TestGlossaryBase):
	def __init__(self: "typing.Self", *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update({
			"004-bar.ldf": "b1aa776d",
		})

	def convert_txt_ldf(self: "typing.Self", fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.txt",
			f"{fname}-2.ldf",
			compareText=f"{fname2}.ldf",
			**convertArgs,
		)


	def convert_ldf_txt(self: "typing.Self", fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.ldf",
			f"{fname}-2.txt",
			compareText=f"{fname2}.txt",
			**convertArgs,
		)

	def test_convert_txt_ldf_1(self: "typing.Self"):
		self.convert_txt_ldf(
			"004-bar",
			"004-bar",
		)

	def test_convert_ldf_txt_1(self: "typing.Self"):
		self.convert_ldf_txt(
			"004-bar",
			"004-bar",
			infoOverride={
				"name": None,
				"input_file_size": None,
			},
		)

if __name__ == "__main__":
	unittest.main()
