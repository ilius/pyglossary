import sys
from os.path import dirname, abspath
import unittest

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from tests.glossary_test import TestGlossaryBase
from pyglossary.glossary import Glossary


class TestGlossaryDictunformat(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update({
			"100-en-fa.dictunformat": "f5f8a9bd",
			"100-en-fa.dictunformat.txt": "57b50313",
		})

	def convert_dictunformat_txt(self, fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.dictunformat",
			f"{fname}-tmp.txt",
			compareText=f"{fname2}.txt",
			**convertArgs
		)

	def test_convert_dictunformat_txt_1(self):
		self.convert_dictunformat_txt(
			"100-en-fa",
			"100-en-fa.dictunformat",
		)


if __name__ == "__main__":
	unittest.main()
