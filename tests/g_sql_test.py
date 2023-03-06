import sys
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from tests.glossary_v2_test import TestGlossaryBase


class TestGlossarySQL(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update({
			"100-en-fa.txt": "f5c53133",
			"100-en-fa.txt.sql": "2da84892",
		})


	def convert_txt_sql(self, fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.txt",
			f"{fname}-2.sql",
			compareText=f"{fname2}.sql",
			**convertArgs,
		)

	def test_convert_txt_sql_1(self):
		self.convert_txt_sql(
			"100-en-fa",
			"100-en-fa.txt",
		)


if __name__ == "__main__":
	unittest.main()
