import os
import sys
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from glossary_v2_test import TestGlossaryBase


class TestGlossaryGetttestPo(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update(
			{
				"100-en-fa.po": "694de186",
				"100-en-fa.po.txt": "f0c3ea53",
			},
		)
		os.environ["CALC_FILE_SIZE"] = "1"

	def convert_txt_po(self, fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.txt",
			f"{fname}-2.po",
			compareText=f"{fname2}.po",
			**convertArgs,
		)

	def convert_po_txt(self, fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.po",
			f"{fname}-2.txt",
			compareText=f"{fname2}.txt",
			**convertArgs,
		)

	def test_convert_txt_po_1(self):
		self.convert_txt_po("100-en-fa", "100-en-fa")

	# TODO
	def test_convert_po_txt_1(self):
		self.convert_po_txt(
			"100-en-fa",
			"100-en-fa.po",
			infoOverride={"input_file_size": None},
		)


if __name__ == "__main__":
	unittest.main()
