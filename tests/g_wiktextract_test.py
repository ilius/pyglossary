import sys
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from glossary_v2_test import TestGlossaryBase


class TestGlossaryWiktextract(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update(
			{
				"wiktextract/10-kaikki-fa-PlacesInIran.jsonl": "f7f4a92f",
				"wiktextract/10-kaikki-fa-PlacesInIran.txt": "29b20845",
				"wiktextract/10-kaikki-fa-PlacesInIran-category.txt": "d12fa9c0",
				"wiktextract/10-kaikki-fa-pos-adv.jsonl": "2ddcbbbd",
				"wiktextract/10-kaikki-fa-pos-adv.txt": "fbaa9972",
			},
		)

	def convert_jsonl_txt(self, fname, fname2, **convertArgs):
		self.convert(
			f"wiktextract/{fname}.jsonl",
			f"{fname}-2.txt",
			compareText=f"wiktextract/{fname2}.txt",
			infoOverride={
				# without this, glos name would become f"wiktextract__{fname}.jsonl"
				"name": f"{fname}.jsonl",
			},
			**convertArgs,
		)

	def test_convert_jsonl_txt_1(self):
		self.convert_jsonl_txt(
			"10-kaikki-fa-PlacesInIran",
			"10-kaikki-fa-PlacesInIran",
		)

	def test_convert_jsonl_txt_1_cats(self):
		self.convert_jsonl_txt(
			"10-kaikki-fa-PlacesInIran",
			"10-kaikki-fa-PlacesInIran-category",
			readOptions={
				"categories": True,
			},
		)

	def test_convert_jsonl_txt_2(self):
		self.convert_jsonl_txt(
			"10-kaikki-fa-pos-adv",
			"10-kaikki-fa-pos-adv",
		)



if __name__ == "__main__":
	unittest.main()
