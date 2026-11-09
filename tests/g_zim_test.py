import os
import sys
import unittest
from os.path import abspath, dirname

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


if __name__ == "__main__":
	unittest.main()
