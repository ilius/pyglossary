import sys
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from tests.glossary_v2_test import TestGlossaryBase


class TestGlossaryXDXFLax(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update({
			"100-cyber_lexicon_en-es.xdxf": "8d9ba394",
			"100-cyber_lexicon_en-es-v3.txt": "4aa05086",
		})

	def convert_xdxf_txt(self, fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.xdxf",
			f"{fname}-tmp.txt",
			compareText=f"{fname2}.txt",
			inputFormat="XdxfLax",
			**convertArgs,
		)

	def test_convert_xdxf_txt_1(self):
		self.convert_xdxf_txt(
			"100-cyber_lexicon_en-es",
			"100-cyber_lexicon_en-es-v3",
		)


if __name__ == "__main__":
	unittest.main()
