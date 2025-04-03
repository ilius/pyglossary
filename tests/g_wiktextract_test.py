import os
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
				"wiktextract/10-kaikki-fa-pos-adv.jsonl": "2ddcbbbd",
				"wiktextract/03-kaikki-fa-selection.jsonl": "31223225",
				"wiktextract/03-kaikki-fa-selection-v3.txt": "9e6dcb38",
				"wiktextract/10-kaikki-fa-PlacesInIran-category-v3.txt": "da7ae87d",
				"wiktextract/10-kaikki-fa-PlacesInIran-v3.txt": "c904b376",
				"wiktextract/10-kaikki-fa-pos-adv-v3.txt": "6bd35c97",
				"wiktextract/10-kaikki-fa-pos-adv-word_title-v3.txt": "3217ea15",
			},
		)
		os.environ["CALC_FILE_SIZE"] = "1"

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
			"10-kaikki-fa-PlacesInIran-v3",
		)

	def test_convert_jsonl_txt_1_cats(self):
		self.convert_jsonl_txt(
			"10-kaikki-fa-PlacesInIran",
			"10-kaikki-fa-PlacesInIran-category-v3",
			readOptions={
				"categories": True,
			},
		)

	def test_convert_jsonl_txt_2(self):
		self.convert_jsonl_txt(
			"10-kaikki-fa-pos-adv",
			"10-kaikki-fa-pos-adv-v3",
		)

	def test_convert_jsonl_txt_2_word_title(self):
		self.convert_jsonl_txt(
			"10-kaikki-fa-pos-adv",
			"10-kaikki-fa-pos-adv-word_title-v3",
			readOptions={
				"word_title": True,
			},
		)

	def test_convert_jsonl_txt_3(self):
		self.convert_jsonl_txt(
			"03-kaikki-fa-selection",
			"03-kaikki-fa-selection-v3",
		)
		# testing these features
		# "antonyms" in sense
		# "topics" in sense
		# "form_of" in sense


if __name__ == "__main__":
	unittest.main()
