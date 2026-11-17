from __future__ import annotations

import sys
import unittest
import warnings
from os.path import abspath, dirname, isdir, isfile, join

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from glossary_v2_test import TestGlossaryBase

from pyglossary.glossary_v2 import Glossary
from pyglossary.text_writer import TextGlossaryWriter, writeTxt


class TestTextWriter(TestGlossaryBase):
	entryFmt = "{word}\t{defi}\n"

	def makeWriter(self, glos: Glossary, **attrs) -> TextGlossaryWriter:
		writer = TextGlossaryWriter(glos, entryFmt=self.entryFmt, writeInfo=False)
		writer.setAttrs(**attrs)
		return writer

	def writeEntries(self, writer: TextGlossaryWriter, filename: str, entries) -> None:
		writer.open(filename)
		gen = writer.write()
		next(gen)
		for entry in entries:
			gen.send(entry)
		try:
			gen.send(None)
		except StopIteration:
			pass
		writer.finish()

	def test_write_entries(self):
		glos = self.glos = Glossary()
		entries = [
			glos.newEntry(["one"], "first"),
			glos.newEntry(["two", "second"], "second defi"),
		]
		filename = self.newTempFilePath("entries.txt")
		writer = self.makeWriter(
			glos,
			resources=False,
			termEscapeFunc=lambda term: term.replace(" ", "_"),
			defiEscapeFunc=lambda defi: defi.upper(),
		)
		self.writeEntries(writer, filename, entries)

		with open(filename, encoding="utf-8") as file:
			self.assertEqual(
				file.read(),
				"one\tFIRST\ntwo|second\tSECOND DEFI\n",
			)

	def test_write_term_list_encode(self):
		glos = self.glos = Glossary()
		entries = [glos.newEntry(["alpha", "beta"], "defi")]
		filename = self.newTempFilePath("term_list.txt")
		writer = self.makeWriter(
			glos,
			resources=False,
			termListEncodeFunc="|".join,
			termEscapeFunc=str.upper,
		)
		self.writeEntries(writer, filename, entries)

		with open(filename, encoding="utf-8") as file:
			self.assertEqual(file.read(), "alpha|beta\tdefi\n")

	def test_write_word_title(self):
		glos = self.glos = Glossary()
		entries = [glos.newEntry(["title-word"], "defi")]
		filename = self.newTempFilePath("word_title.txt")
		writer = self.makeWriter(glos, resources=False, word_title=True)
		self.writeEntries(writer, filename, entries)

		expected = f"title-word\t{glos.wordTitleStr('title-word')}defi\n"
		with open(filename, encoding="utf-8") as file:
			self.assertEqual(file.read(), expected)

	def test_write_data_entries(self):
		glos = self.glos = Glossary()
		entries = [
			glos.newEntry(["word"], "defi"),
			glos.newDataEntry("img/icon.png", b"PNG"),
		]
		filename = self.newTempFilePath("with_data.txt")
		writer = self.makeWriter(glos, resources=True)
		self.writeEntries(writer, filename, entries)

		self.assertTrue(isfile(join(f"{filename}_res", "img", "icon.png")))

	def test_write_data_entries_skipped(self):
		glos = self.glos = Glossary()
		entries = [
			glos.newEntry(["word"], "defi"),
			glos.newDataEntry("img/icon.png", b"PNG"),
		]
		filename = self.newTempFilePath("no_data.txt")
		writer = self.makeWriter(glos, resources=False)
		self.writeEntries(writer, filename, entries)

		self.assertFalse(isdir(f"{filename}_res"))
		with open(filename, encoding="utf-8") as file:
			self.assertEqual(file.read(), "word\tdefi\n")

	def test_write_no_res_dir_without_data_entries(self):
		glos = self.glos = Glossary()
		entries = [glos.newEntry(["word"], "defi")]
		filename = self.newTempFilePath("no_res.txt")
		writer = self.makeWriter(glos, resources=True)
		self.writeEntries(writer, filename, entries)

		self.assertFalse(isdir(f"{filename}_res"))
		with open(filename, encoding="utf-8") as file:
			self.assertEqual(file.read(), "word\tdefi\n")

	def test_write_skip_resources_config(self):
		glos = self.glos = Glossary()
		glos.config = {"skip_resources": True}
		entries = [
			glos.newEntry(["word"], "defi"),
			glos.newDataEntry("img/icon.png", b"PNG"),
		]
		filename = self.newTempFilePath("skip_resources.txt")
		writer = self.makeWriter(glos, resources=True)
		self.writeEntries(writer, filename, entries)

		self.assertFalse(isdir(f"{filename}_res"))
		with open(filename, encoding="utf-8") as file:
			self.assertEqual(file.read(), "word\tdefi\n")

	def test_write_file_size_split(self):
		glos = self.glos = Glossary()
		entries = [
			glos.newEntry([f"word{index}"], f"defi{index}") for index in range(250)
		]
		filename = self.newTempFilePath("split.txt")
		writer = self.makeWriter(
			glos,
			resources=False,
			file_size_approx=1,
			tail="END\n",
		)
		with warnings.catch_warnings():
			warnings.simplefilter("ignore", ResourceWarning)
			self.writeEntries(writer, filename, entries)

		self.assertTrue(isfile(filename))
		self.assertTrue(isfile(f"{filename}.1"))
		self.assertTrue(isfile(f"{filename}.2"))

		with open(f"{filename}.2", encoding="utf-8") as file:
			self.assertTrue(file.read().endswith("END\n"))

	def test_write_info_skips_empty(self):
		glos = self.glos = Glossary()
		glos.setInfo("name", "Name")
		glos.setInfo("description", "Desc")
		glos.setInfo("author", "Author")
		glos.setInfo("copyright", "Copyright")
		glos.setInfo("", "empty-key")
		glos.setInfo("empty-value", "")
		filename = self.newTempFilePath("info.txt")
		writer = TextGlossaryWriter(
			glos,
			entryFmt=self.entryFmt,
			writeInfo=True,
			outInfoKeysAliasDict={"description": ""},
		)
		writer.setAttrs(
			resources=False,
			termEscapeFunc=lambda term: "" if term == "##name" else term,
			defiEscapeFunc=lambda defi: "" if defi == "Author" else defi,
		)
		with self.assertLogs("pyglossary", level="WARNING"):
			self.writeEntries(writer, filename, [])

		with open(filename, encoding="utf-8") as file:
			self.assertEqual(file.read(), "##copyright\tCopyright\n")

	def test_write_missing_entry_fmt(self):
		glos = self.glos = Glossary()
		with self.assertRaises(ValueError):
			TextGlossaryWriter(glos, entryFmt="")

	def test_write_txt(self):
		glos = self.glos = Glossary()
		entries = [glos.newEntry(["word"], "defi")]
		filename = self.newTempFilePath("wrapped.out")
		gen = writeTxt(
			glos,
			entryFmt=self.entryFmt,
			filename=filename,
			writeInfo=False,
			head="HEAD\n",
			tail="TAIL\n",
			ext=".out",
			encoding="utf-8",
			newline="\n",
			resources=False,
		)
		next(gen)
		for entry in entries:
			gen.send(entry)
		try:
			gen.send(None)
		except StopIteration:
			pass

		with open(filename, encoding="utf-8") as file:
			self.assertEqual(file.read(), "HEAD\nword\tdefi\nTAIL\n")

	def test_write_txt_default_filename(self):
		glos = self.glos = Glossary()
		source = self.newTempFilePath("default-name.txt")
		gen = writeTxt(
			glos,
			entryFmt=self.entryFmt,
			filename=source,
			writeInfo=False,
			resources=False,
		)
		next(gen)
		gen.send(glos.newEntry(["word"], "defi"))
		try:
			gen.send(None)
		except StopIteration:
			pass

		glos2 = Glossary()
		try:
			glos2.directRead(source)
			gen = writeTxt(
				glos2,
				entryFmt=self.entryFmt,
				writeInfo=False,
				ext=".out",
				resources=False,
			)
			next(gen)
			gen.send(glos2.newEntry(["word"], "defi"))
			try:
				gen.send(None)
			except StopIteration:
				pass
		finally:
			glos2.cleanup()
			glos2.clear()

		self.assertTrue(isfile(source[: -len(".txt")] + ".out"))


if __name__ == "__main__":
	unittest.main()
