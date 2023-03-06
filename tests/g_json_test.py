import sys
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from tests.glossary_v2_test import TestGlossaryBase


class TestGlossaryJSON(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update({
			"004-bar.json": "7e4b2663",
			"100-en-de.json": "6fa8e159",
			"100-en-fa.json": "8d29c1be",
			"100-ja-en.json": "fab2c106",
		})

	def convert_txt_json(self, fname):
		self.convert(
			f"{fname}.txt",
			f"{fname}-2.json",
			compareText=f"{fname}.json",
		)

	def test_convert_txt_json_0(self):
		self.convert_txt_json("004-bar")

	def test_convert_txt_json_1(self):
		self.convert_txt_json("100-en-fa")

	def test_convert_txt_json_2(self):
		self.convert_txt_json("100-en-de")

	def test_convert_txt_json_3(self):
		self.convert_txt_json("100-ja-en")


if __name__ == "__main__":
	unittest.main()
