import hashlib
import shutil
import unittest
from bisect import bisect_left
from os.path import join

from glossary_v2_test import TestGlossaryBase

from pyglossary.glossary_v2 import ConvertArgs, Glossary
from pyglossary.plugin_lib.dictdlib import DictDB
from pyglossary.plugins.dict_org.reader import Reader


class TestGlossaryDictOrg(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

		self.dataFile |= {
			"5-fa-en.txt",
			"5-fa-en.txt.dict",
			"5-fa-en.txt.index",
			"5-fa-en.txt.index.txt",
			"5-en-en-utf8.txt",
			"5-en-en-utf8.txt.dict",
			"5-en-en-utf8.txt.index",
			"5-en-en-utf8.txt.index.txt",
		}

	def convert_txt_dict_org(self, fname, fname2, dictSha1="", **convertArgs):
		self.convert(
			f"{fname}.txt",
			f"{fname}-2.index",
			compareText=f"{fname2}.index",
			**convertArgs,
		)
		if dictSha1:
			dictPath = join(self.tempDir, f"{fname}-2.dict")
			with open(dictPath, mode="rb") as file:
				actualSha1 = hashlib.sha1(file.read()).hexdigest()
			self.assertEqual(dictSha1, actualSha1, dictPath)

	def convert_dict_org_txt(self, fname, fname2, **convertArgs):
		self.downloadFile(f"{fname}.dict")
		self.convert(
			f"{fname}.index",
			f"{fname}-2.txt",
			compareText=f"{fname2}.txt",
			**convertArgs,
		)

	def test_convert_txt_dict_org_fa_en(self):
		self.convert_txt_dict_org(
			"5-fa-en",
			"5-fa-en.txt",
			dictSha1="71b0db987dd52b8b0bc6dd4f0c720c15a06f2fa6",
			writeOptions={"install": False},
		)

	def test_convert_dict_org_txt_fa_en(self):
		self.convert_dict_org_txt(
			"5-fa-en.txt",
			"5-fa-en.txt.index",
			infoOverride={"input_file_size": None},
		)

	def test_convert_txt_dict_org_utf8_terms(self):
		self.convert_txt_dict_org(
			"5-en-en-utf8",
			"5-en-en-utf8.txt",
			dictSha1="c60466c4a3b219d16acbba2a8946bc8aedeedc1c",
			writeOptions={"install": False},
		)
		self.compareBinaryFiles(
			join(self.tempDir, "5-en-en-utf8-2.dict"),
			self.downloadFile("5-en-en-utf8.txt.dict"),
		)
		with open(join(self.tempDir, "5-en-en-utf8-2.index"), "rb") as file:
			keys = [line.split(b"\t", 1)[0] for line in file]
		# dictd binary-searches UTF-8 keys using byte comparisons. Queries
		# are lowercase and punctuation-free, while accents are retained.
		self.assertEqual(keys, sorted(keys))
		for query in ("apple", "café", "icecream", "zebra", "éclair"):
			with self.subTest(query=query):
				key = query.encode("utf-8")
				pos = bisect_left(keys, key)
				self.assertLess(pos, len(keys))
				self.assertEqual(keys[pos], key)

	def test_convert_dict_org_txt_utf8_terms(self):
		self.convert_dict_org_txt(
			"5-en-en-utf8.txt",
			"5-en-en-utf8.txt.index",
			infoOverride={"input_file_size": None},
		)

	def test_convert_dict_org_txt_metadata(self):
		for hyphenated in (False, True):
			with self.subTest(hyphenated=hyphenated):
				base = join(self.tempDir, f"metadata-{hyphenated}")
				for ext in ("dict", "index"):
					shutil.copyfile(
						self.downloadFile(f"5-en-en-utf8.txt.{ext}"),
						f"{base}.{ext}",
					)
				db = DictDB(base, "update", 1)
				for name, value in {
					"url": "https://example.org/dictionary",
					"short": "Synthetic sample",
					"info": "Synthetic dictionary description.\nSecond line.",
				}.items():
					word = f"00-database-{name}"
					definition = f"{word}\n     {value}" if hyphenated else value
					db.addEntry(definition, [word])
				db.addEntry("abcdefghijklmnopqrstuvwxyzé", ["00-database-alphabet"])
				db.addEntry("", ["00-database-dictfmt-test"])
				db.finish()
				if hyphenated:
					with open(f"{base}.index", encoding="utf-8") as file:
						index = file.read()
					with open(f"{base}.index", "w", encoding="utf-8") as file:
						file.write(index.replace("00database", "00-database-"))

				glos = self.glos = Glossary()
				reader = Reader(glos)
				reader.open(f"{base}.index")
				try:
					self.assertEqual(len(reader), 5)
				finally:
					reader.close()
				output = f"{base}.txt"
				self.assertEqual(
					glos.convert(
						ConvertArgs(
							inputFilename=f"{base}.index",
							outputFilename=output,
							infoOverride={"input_file_size": None},
						),
					),
					output,
				)
				with open(output, encoding="utf-8") as file:
					lines = file.readlines()
				self.assertIn("##name\tSynthetic sample\n", lines)
				self.assertIn("##website\thttps://example.org/dictionary\n", lines)
				self.assertIn(
					"##description\tSynthetic dictionary description.\\nSecond line.\n",
					lines,
				)
				entries = [line for line in lines if not line.startswith("##")]
				with open(
					self.downloadFile("5-en-en-utf8.txt.index.txt"),
					encoding="utf-8",
				) as file:
					expected = [line for line in file if not line.startswith("##")]
				self.assertEqual(entries, expected)
				glos.cleanup()
				glos.clear()


if __name__ == "__main__":
	unittest.main()
