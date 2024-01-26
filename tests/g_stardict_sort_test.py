import unittest

from g_stardict_test import TestGlossaryStarDictBase
from glossary_errors_test import TestGlossaryErrorsBase


class TestGlossaryStarDictSortCustom(TestGlossaryStarDictBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryErrorsBase.__init__(self, *args, **kwargs)
		self.dataFileCRC32.update(
			{
				"100-en-fa.sd/100-en-fa.dict": "223a0d1d",
				"100-en-fa.sd/100-en-fa.idx": "6df43378",
				"100-en-fa.sd/100-en-fa.ifo": "3f2086cd",
				"100-en-fa.sd/100-en-fa.syn": "1160fa0b",
				"100-en-fa-sd.txt": "85f9d3fc",
			},
		)

	def convert_txt_stardict_enfa(
		self,
		fname,
		**convertArgs,
	):
		self.convert_txt_stardict(
			fname,
			config={"enable_alts": True},
			info={
				"sourceLang": "English",
				"targetLang": "Persian",
			},
			**convertArgs,
		)

	def convert_txt_stardict_enfa_1(self):
		sortKeyName = "headword"
		self.convert_txt_stardict_enfa(
			"100-en-fa",
			sortKeyName=sortKeyName,
			sqlite=True,
		)
		self.assertLogWarning(
			f"Ignoring user-defined sort order {sortKeyName!r}"
			f", and using sortKey function from Stardict plugin",
		)

	def test_convert_txt_stardict_enfa_2(self):
		sortKeyName = "ebook"
		self.convert_txt_stardict_enfa(
			"100-en-fa",
			sortKeyName=sortKeyName,
			sqlite=False,
		)
		self.assertLogWarning(
			f"Ignoring user-defined sort order {sortKeyName!r}"
			f", and using sortKey function from Stardict plugin",
		)

	def test_convert_txt_stardict_enfa_3(self):
		sortKeyName = "stardict:en_US.UTF-8"
		self.convert_txt_stardict_enfa(
			"100-en-fa",
			sortKeyName=sortKeyName,
			sqlite=True,
		)
		self.assertLogWarning(
			f"Ignoring user-defined sort order {sortKeyName!r}"
			f", and using sortKey function from Stardict plugin",
		)

	def test_convert_txt_stardict_enfa_4(self):
		sortKeyName = "stardict:fa_IR.UTF-8"
		self.convert_txt_stardict_enfa(
			"100-en-fa",
			sortKeyName=sortKeyName,
			sqlite=False,
		)
		self.assertLogWarning(
			f"Ignoring user-defined sort order {sortKeyName!r}"
			f", and using sortKey function from Stardict plugin",
		)


if __name__ == "__main__":
	unittest.main()
