import sys
import unittest
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)


from g_stardict_test import TestGlossaryStarDictBase
from glossary_v2_errors_test import TestGlossaryErrorsBase

__all__ = ["TestGlossaryStarDictMergeSyns"]


class TestGlossaryStarDictMergeSyns(TestGlossaryStarDictBase):
	def convert_txt_stardict(self, *args, **kwargs):
		kwargs["outputFormat"] = "StardictMergeSyns"
		TestGlossaryStarDictBase.convert_txt_stardict(self, *args, **kwargs)

	def __init__(self, *args, **kwargs):
		TestGlossaryErrorsBase.__init__(self, *args, **kwargs)

		self.dataFileCRC32.update(
			{
				"002-plain-html.txt": "75484314",
				"004-plain-html-alts.txt": "505d4675",
				"002-plain-html-sd-merge-syns-v2/002-plain-html.dict": "2e9d20d8",
				"002-plain-html-sd-merge-syns-v2/002-plain-html.idx": "3956ad72",
				"002-plain-html-sd-merge-syns-v2/002-plain-html.ifo": "1991f125",
				"004-plain-html-alts-sd-merge-syns-v2/004-plain-html-alts.dict": "889f11f8",
				"004-plain-html-alts-sd-merge-syns-v2/004-plain-html-alts.idx": "092ba555",
				"004-plain-html-alts-sd-merge-syns-v2/004-plain-html-alts.ifo": "628abe99",
				# "004-plain-html-alts-sd-merge-syns-v2/004-plain-html-alts.syn": "c07f7111",
				"100-en-de-v4-sd-merge-syns-v2/100-en-de-v4.dict": "5a97476f",
				"100-en-de-v4-sd-merge-syns-v2/100-en-de-v4.idx": "a99f29d2",
				"100-en-de-v4-sd-merge-syns-v2/100-en-de-v4.ifo": "2120708c",
				"100-en-fa-sd-merge-syns-v2/100-en-fa.dict": "223a0d1d",
				"100-en-fa-sd-merge-syns-v2/100-en-fa.idx": "13f1c7af",
				"100-en-fa-sd-merge-syns-v2/100-en-fa.ifo": "248ef828",
			},
		)

	def test_convert_txt_stardict_1_merge_syns(self):
		self.convert_txt_stardict(
			"100-en-fa",
			"100-en-fa-sd-merge-syns-v2",
			syn=False,
			# dictzip=False,
		)

	def test_convert_txt_stardict_3_merge_syns(self):
		self.convert_txt_stardict(
			"100-en-de-v4",
			"100-en-de-v4-sd-merge-syns-v2",
			syn=False,
			# dictzip=False,
		)

	def test_convert_txt_stardict_general_1_merge_syns(self):
		self.convert_txt_stardict(
			"002-plain-html",
			"002-plain-html-sd-merge-syns-v2",
			syn=False,
			# dictzip=False,
		)

	def test_convert_txt_stardict_general_2_merge_syns(self):
		self.convert_txt_stardict(
			"004-plain-html-alts",
			"004-plain-html-alts-sd-merge-syns-v2",
			syn=False,
			# dictzip=False,
		)


if __name__ == "__main__":
	unittest.main()
