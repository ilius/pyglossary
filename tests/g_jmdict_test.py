import sys
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from tests.glossary_v2_test import TestGlossaryBase


class TestGlossaryJMdict(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update({
			"050-JMdict-English": "aec9ad8c",
			"050-JMdict-English.txt": "edd13a27",
		})

	def convert_jmdict_txt(self, fname, fname2, **convertArgs):
		self.convert(
			fname,
			f"{fname}-2.txt",
			compareText=f"{fname2}.txt",
			inputFormat="JMDict",
			**convertArgs,
		)

	def test_convert_jmdict_txt_1(self):
		self.convert_jmdict_txt(
			"050-JMdict-English",
			"050-JMdict-English",
		)


if __name__ == "__main__":
	unittest.main()
