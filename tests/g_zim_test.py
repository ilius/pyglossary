import os
import random
import sys
import unittest
from os.path import abspath, dirname, join
from urllib.parse import unquote

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from glossary_v2_test import TestGlossaryBase

from pyglossary.glossary_v2 import ConvertArgs, Glossary

try:
	from libzim.reader import Archive
except ModuleNotFoundError:
	Archive = None


class TestGlossaryZimWrite(TestGlossaryBase):
	def __init__(self, *args, **kwargs):
		TestGlossaryBase.__init__(self, *args, **kwargs)

	def setUp(self):
		TestGlossaryBase.setUp(self)

	@staticmethod
	def _readTxtHeadwords(filename: str) -> list[str]:
		glos = Glossary()
		try:
			glos.directRead(filename)
			return [entry.s_term for entry in glos if not entry.isData()]
		finally:
			glos.cleanup()
			glos.clear()

	@staticmethod
	def _zimArticleHeadwords(filename: str) -> list[str]:
		archive = Archive(filename)
		headwords = []
		for entryId in range(archive.entry_count):
			path = archive.get_entry_by_id(entryId).path
			if path.startswith("A/"):
				headwords.append(unquote(path[len("A/") :]))
		return headwords

	@unittest.skipUnless(Archive, "libzim is not installed")
	def test_convert_txt_zim_1(self):
		fname = "100-en-fa"
		outputFilename = self.newTempFilePath(f"{fname}.zim")
		self.convert(
			f"{fname}.txt",
			f"{fname}.zim",
			writeOptions={
				"compress": False,
				"indexing": False,
			},
		)
		self.assertTrue(os.path.isfile(outputFilename))

		archive = Archive(outputFilename)
		self.assertGreaterEqual(archive.entry_count, 100)
		self.assertEqual(
			archive.get_metadata("Name").decode("utf-8"),
			"Sample: Aryanpour (2021) (en-fa, fa-en)",
		)
		self.assertEqual(archive.get_metadata("Language").decode("utf-8"), "eng")

		entry = archive.get_entry_by_path("A/a")
		self.assertEqual(entry.title, "a")
		content = entry.get_item().content.tobytes().decode("utf-8")
		self.assertIn("indefinite article", content)

		entry = archive.get_entry_by_title("A")
		content = entry.get_item().content.tobytes().decode("utf-8")
		self.assertIn('href="A/ABO%20system"', content)

	@unittest.skipUnless(Archive, "libzim is not installed")
	def test_convert_txt_zim_2_word_title(self):
		fname = "100-en-fa"
		outputFilename = self.newTempFilePath(f"{fname}.zim")
		self.convert(
			f"{fname}.txt",
			f"{fname}.zim",
			writeOptions={
				"compress": False,
				"indexing": False,
				"word_title": True,
			},
		)
		archive = Archive(outputFilename)
		entry = archive.get_entry_by_title("a")
		content = entry.get_item().content.tobytes().decode("utf-8")
		self.assertTrue(content.startswith("<b>a</b><br>"))

	@unittest.skipUnless(Archive, "libzim is not installed")
	def test_convert_txt_zim_compress_option(self):
		fname = "100-en-fa"
		sizes = {}
		for compress in (True, False):
			outputFilename = self.newTempFilePath(f"{fname}-compress-{compress}.zim")
			self.convert(
				f"{fname}.txt",
				f"{fname}-compress-{compress}.zim",
				writeOptions={
					"compress": compress,
					"indexing": False,
				},
			)
			sizes[compress] = os.path.getsize(outputFilename)
			archive = Archive(outputFilename)
			content = archive.get_entry_by_path("A/a").get_item().content
			self.assertIn("indefinite article", content.tobytes().decode("utf-8"))
		self.assertGreater(sizes[False], sizes[True])

	@unittest.skipUnless(Archive, "libzim is not installed")
	def test_convert_bword_links_percent_encoded_and_fragment(self):
		inputFilename = self.newTempFilePath("zim-bword-links.txt")
		with open(inputFilename, mode="w", encoding="utf-8") as file:
			file.write('a\t<a href="bword://ABO%20system#sec-1">x</a>\n')
			file.write("ABO system\tdefinition\n")
		outputFilename = self.newTempFilePath("zim-bword-links.zim")
		glos = self.glos = Glossary()
		glos.convert(
			ConvertArgs(
				inputFilename=inputFilename,
				outputFilename=outputFilename,
				writeOptions={"indexing": False},
			),
		)
		archive = Archive(outputFilename)
		content = archive.get_entry_by_path("A/a").get_item().content
		self.assertIn(
			'href="A/ABO%20system#sec-1"',
			content.tobytes().decode("utf-8"),
		)

	@unittest.skipUnless(Archive, "libzim is not installed")
	def test_convert_txt_zim_sort_ignored(self):
		fname = "100-en-fa"

		def entryPaths(zimFilename: str) -> list[str]:
			archive = Archive(zimFilename)
			return [archive.get_entry_by_id(i).path for i in range(archive.entry_count)]

		plainFilename = self.newTempFilePath(f"{fname}-plain.zim")
		self.convert(
			f"{fname}.txt",
			f"{fname}-plain.zim",
			writeOptions={"indexing": False},
		)
		plainPaths = entryPaths(plainFilename)

		sortedFilename = self.newTempFilePath(f"{fname}-sorted.zim")
		self.convert(
			f"{fname}.txt",
			f"{fname}-sorted.zim",
			writeOptions={"indexing": False},
			sort=True,
		)
		sortedPaths = entryPaths(sortedFilename)
		self.assertEqual(plainPaths, sortedPaths)
		self.assertEqual(sortedPaths, sorted(sortedPaths, key=lambda p: p.encode()))

	@unittest.skipUnless(Archive, "libzim is not installed")
	def test_convert_txt_zim_random_input_order(self):
		# ASCII-only terms: ZIM sorts by percent-encoded path, which
		# matches plain code point order for these.
		terms = [
			"apple",
			"Banana",
			"cherry",
			"date",
			"elderberry",
			"fig",
			"grape",
			"honeydew",
			"kiwi",
			"lemon",
		]
		expected = sorted(terms)
		for seed in range(3):
			shuffled = terms[:]
			random.Random(seed).shuffle(shuffled)
			self.assertNotEqual(shuffled, expected)

			inputFilename = self.newTempFilePath(f"zim-random-order-{seed}.txt")
			with open(inputFilename, mode="w", encoding="utf-8") as file:
				file.writelines(f"{term}\tdefinition of {term}\n" for term in shuffled)
			outputFilename = self.newTempFilePath(f"zim-random-order-{seed}.zim")
			glos = self.glos = Glossary()
			glos.convert(
				ConvertArgs(
					inputFilename=inputFilename,
					outputFilename=outputFilename,
					writeOptions={"indexing": False},
				),
			)
			self.assertEqual(
				self._zimArticleHeadwords(outputFilename),
				expected,
				msg=f"{seed=}",
			)

	@unittest.skipUnless(Archive, "libzim is not installed")
	def test_sort_key_zim_matches_zim_order(self):
		# This fixture has no duplicate headwords or alternate terms.
		fname = "100-en-de-v4"
		self.convert(
			f"{fname}.txt",
			f"{fname}-sort-key.zim",
			writeOptions={"indexing": False},
		)
		expected = self._zimArticleHeadwords(
			join(self.tempDir, f"{fname}-sort-key.zim"),
		)
		self.assertEqual(len(expected), 100)
		self.assertEqual(len(expected), len(set(expected)))

		for sqlite in (None, True, False):
			outputName = f"{fname}-sort-key-{sqlite}.txt"
			self.convert(
				f"{fname}.txt",
				outputName,
				sort=True,
				sortKeyName="zim",
				sqlite=sqlite,
			)
			self.assertEqual(
				self._readTxtHeadwords(join(self.tempDir, outputName)),
				expected,
				msg=f"{sqlite=}",
			)

		os.environ["NO_SQLITE"] = "1"
		try:
			outputName = f"{fname}-sort-key-nosqlite.txt"
			self.convert(
				f"{fname}.txt",
				outputName,
				sort=True,
				sortKeyName="zim",
				sqlite=False,
			)
			self.assertEqual(
				self._readTxtHeadwords(join(self.tempDir, outputName)),
				expected,
			)
		finally:
			del os.environ["NO_SQLITE"]

	@unittest.skipUnless(Archive, "libzim is not installed")
	def test_convert_txt_zim_txt_matches_zim_sort_key(self):
		# This fixture has no duplicate headwords or alternate terms.
		fname = "100-en-de-v4"

		sortedName = f"{fname}-sort-key.txt"
		self.convert(
			f"{fname}.txt",
			sortedName,
			sort=True,
			sortKeyName="zim",
		)
		expected = self._readTxtHeadwords(join(self.tempDir, sortedName))

		zimName = f"{fname}-roundtrip.zim"
		self.convert(
			f"{fname}.txt",
			zimName,
			writeOptions={"indexing": False},
		)

		outputFilename = self.newTempFilePath(f"{fname}-roundtrip.txt")
		glos = self.glos = Glossary()
		glos.convert(
			ConvertArgs(
				inputFilename=join(self.tempDir, zimName),
				outputFilename=outputFilename,
			),
		)
		self.assertEqual(self._readTxtHeadwords(outputFilename), expected)


if __name__ == "__main__":
	unittest.main()
