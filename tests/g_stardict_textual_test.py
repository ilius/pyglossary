import sys
from os.path import dirname, abspath
import unittest

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from tests.glossary_test import TestGlossaryBase
from pyglossary.glossary import Glossary


class TestGlossaryStarDictTextual(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update({
			"100-en-fa-sdt.xml": "48cb3336",
			"100-en-fa-sdt.xml.txt": "0c9b4025",

			"stardict-mixed-types-1.xml": "55da713d",
			"stardict-mixed-types-1.xml.txt": "0460bc7e",
		})

	def convert_txt_sdxml(self, fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.txt",
			f"{fname}-2.xml",
			compareText=f"{fname2}.xml",
			outputFormat="StardictTextual",
			**convertArgs
		)

	def convert_sdxml_txt(self, fname, fname2, **convertArgs):
		self.convert(
			f"{fname}.xml",
			f"{fname}-2.txt",
			compareText=f"{fname2}.txt",
			inputFormat="StardictTextual",
			**convertArgs
		)

	def test_convert_txt_sdxml_1(self):
		self.convert_txt_sdxml(
			"100-en-fa",
			"100-en-fa-sdt",
		)

	def test_convert_sdxml_txt_1(self):
		self.convert_sdxml_txt(
			"100-en-fa-sdt",
			"100-en-fa-sdt.xml",
		)

	def test_convert_sdxml_txt_2(self):
		self.convert_sdxml_txt(
			"stardict-mixed-types-1",
			"stardict-mixed-types-1.xml",
		)

