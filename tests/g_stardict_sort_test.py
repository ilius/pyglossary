import hashlib
import os
import unittest

from g_stardict_test import TestGlossaryStarDictBase
from glossary_v2_errors_test import TestGlossaryErrorsBase

from pyglossary.glossary_v2 import Glossary


class TestGlossaryStarDictSortCustom(TestGlossaryStarDictBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryErrorsBase.__init__(self, *args, **kwargs)
		self.dataFileCRC32.update(
			{
				"100-en-fa-sd-v2/100-en-fa.dict": "223a0d1d",
				"100-en-fa-sd-v2/100-en-fa.idx": "6df43378",
				"100-en-fa-sd-v2/100-en-fa.ifo": "bb916827",
				"100-en-fa-sd-v2/100-en-fa.syn": "1160fa0b",
				"100-en-fa-sd-v2.txt": "0b8b2ac0",
			},
		)

	def convert_txt_stardict_enfa(
		self,
		fname,
		**convertArgs,
	):
		self.convert_txt_stardict(
			fname,
			fname + "-sd-v2",
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
			", and using sortKey function from Stardict plugin",
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
			", and using sortKey function from Stardict plugin",
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
			", and using sortKey function from Stardict plugin",
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
			", and using sortKey function from Stardict plugin",
		)

	def test_convert_txt_stardict_enfa_5(self):
		os.environ["NO_SQLITE"] = "1"
		self.convert_txt_stardict_enfa("100-en-fa", sqlite=False)
		del os.environ["NO_SQLITE"]

	def test_write_manual(self):
		gloss = Glossary()
		gloss.setInfo("title", "repro")

		gloss.addEntry(gloss.newEntry(["Z", "ZZ"], "Z"))
		gloss.addEntry(gloss.newEntry(["A", "AA"], "A"))

		baseName = "test_write_manual"

		sha1ByExt = {
			"ifo": "7e786a6c95eda8a6a88804ab5c1ea16a3f22132c",
			"idx": "656012a08c8283433ce566150c38ed1d0be9dcdc",
			"dict": "0c9d125b39f8a674cee51c774d4f144fc452ab31",
			"syn": "5349fa18cd1558ff04c18316b412b2692eb45ca2",
		}
		pathByExt = {
			ext: self.newTempFilePath(f"{baseName}.{ext}") for ext in sha1ByExt
		}

		gloss.write(pathByExt["ifo"], formatName="Stardict", dictzip=False)

		for ext, sha1sum in sha1ByExt.items():
			with open(pathByExt[ext], mode="rb") as file:
				actualSha1 = hashlib.sha1(file.read()).hexdigest()
				self.assertEqual(sha1sum, actualSha1, f"{ext=}")


if __name__ == "__main__":
	unittest.main()
