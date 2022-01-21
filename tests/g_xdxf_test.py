import sys
from os.path import dirname, abspath
import unittest

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from tests.glossary_test import TestGlossaryBase


class TestGlossaryXDXF(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update({
			"100-cyber_lexicon_en-es.txt": "8571e444",
			"100-cyber_lexicon_en-es.xdxf": "8d9ba394"
		})

	def convert_xdxf_txt(self, fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.xdxf",
			f"{fname}-2.txt",
			compareText=f"{fname2}.txt",
			**convertArgs
		)

	def test_convert_xdxf_txt_1(self):
		self.convert_xdxf_txt(
			"100-cyber_lexicon_en-es",
			"100-cyber_lexicon_en-es",
		)


if __name__ == "__main__":
	unittest.main()
