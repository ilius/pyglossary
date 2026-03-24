#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Integration tests for PocketBook SDIC writer plugin."""

from __future__ import annotations

import os
import struct
import sys
import tempfile
import unittest
import zlib
from os.path import abspath, dirname

rootDir = dirname(dirname(abspath(__file__)))
sys.path.insert(0, rootDir)

from pyglossary.glossary_v2 import Glossary


def _parse_sdic(path: str) -> dict:
	"""Parse an SDIC file and return its structure for verification."""
	with open(path, "rb") as f:
		data = f.read()

	result: dict = {}
	result["signature"] = data[:4]
	result["version"] = struct.unpack_from("<I", data, 4)[0]
	result["entry_count"] = struct.unpack_from("<I", data, 8)[0]
	result["max_entry_size"] = struct.unpack_from("<I", data, 0x0C)[0]
	result["collate_off"] = struct.unpack_from("<I", data, 0x24)[0]
	result["morphems_off"] = struct.unpack_from("<I", data, 0x28)[0]
	result["keyboard_off"] = struct.unpack_from("<I", data, 0x2C)[0]
	result["sparse_off"] = struct.unpack_from("<I", data, 0x38)[0]
	result["data_off"] = struct.unpack_from("<I", data, 0x3C)[0]
	result["name"] = data[0x40:0x80].split(b"\x00")[0].decode("utf-8")
	result["file_size"] = len(data)

	# Parse sparse index
	si_data = data[result["sparse_off"] : result["data_off"]]
	si_raw = zlib.decompress(si_data[4:])
	block_info: list[tuple[int, str]] = []
	off = 0
	while off < len(si_raw) - 1:
		csize = struct.unpack_from("<H", si_raw, off)[0]
		if csize == 0:
			break
		off += 2
		nul = si_raw.index(0, off)
		word = si_raw[off:nul].decode("utf-8")
		off = nul + 1
		block_info.append((csize, word))
	result["blocks"] = block_info

	# Parse all entries from data blocks
	entries: list[tuple[str, str]] = []
	file_offset = result["data_off"]
	for bsize, _first_word in block_info:
		block_raw = zlib.decompress(data[file_offset : file_offset + bsize])
		entry_off = 0
		while entry_off < len(block_raw):
			entry_start = entry_off
			entry_size = struct.unpack_from("<H", block_raw, entry_off)[0]
			if entry_size == 0:
				break
			entry_off += 2
			nul = block_raw.index(0, entry_off)
			word = block_raw[entry_off:nul].decode("utf-8")
			entry_off = nul + 1
			body_end = entry_start + entry_size
			body = block_raw[entry_off:body_end]
			# Strip body markers: 0x20 prefix, 0x20 0x0A 0x00 suffix
			body_text = body[1:-3].decode("utf-8") if len(body) > 4 else ""
			entries.append((word, body_text))
			entry_off = body_end
		file_offset += bsize

	result["entries"] = entries
	return result


class TestPocketBookSdicWriter(unittest.TestCase):
	"""Integration tests for PocketBook SDIC writer."""

	@classmethod
	def setUpClass(cls):
		Glossary.init()

	def setUp(self):
		self.tmpdir = tempfile.mkdtemp()
		self.glos = None

	def tearDown(self):
		if self.glos is not None:
			self.glos.cleanup()
			self.glos.clear()
		import shutil

		shutil.rmtree(self.tmpdir, ignore_errors=True)

	def _write_sdic(self, entries, bookname="Test", **write_options):
		"""Helper: create a glossary, add entries, write to SDIC."""
		self.glos = glos = Glossary()
		glos.setInfo("bookname", bookname)
		for terms, defi in entries:
			if isinstance(terms, str):
				terms = [terms]
			glos.addEntry(glos.newEntry(terms, defi))
		outpath = os.path.join(self.tmpdir, "test.dic")
		glos.write(outpath, formatName="PocketBookSdic", **write_options)
		return outpath

	def test_basic_conversion(self):
		"""Basic TXT-like entries convert to valid SDIC."""
		outpath = self._write_sdic(
			[
				("hello", "world"),
				("test", "definition"),
				("apple", "a fruit"),
			]
		)
		result = _parse_sdic(outpath)
		self.assertEqual(result["signature"], b"SDIC")
		self.assertEqual(result["version"], 0x101)
		self.assertEqual(result["entry_count"], 3)
		self.assertEqual(result["name"], "Test")
		# Entries should be sorted by collated key
		words = [e[0] for e in result["entries"]]
		self.assertEqual(words, ["apple", "hello", "test"])

	def test_html_definitions(self):
		"""HTML markup is preserved verbatim."""
		outpath = self._write_sdic(
			[
				("bold", "<b>strong text</b>"),
				("italic", "<i>emphasis</i>"),
				("mixed", "<b>bold</b> and <i>italic</i> with <br>break"),
			]
		)
		result = _parse_sdic(outpath)
		entries = dict(result["entries"])
		self.assertEqual(entries["bold"], "<b>strong text</b>")
		self.assertEqual(entries["italic"], "<i>emphasis</i>")
		self.assertIn("<b>bold</b>", entries["mixed"])
		self.assertIn("<br>", entries["mixed"])

	def test_html_entities_preserved(self):
		"""HTML entities are preserved as-is."""
		outpath = self._write_sdic(
			[
				("entities", "&amp; &lt; &gt; &quot;"),
			]
		)
		result = _parse_sdic(outpath)
		entries = dict(result["entries"])
		self.assertEqual(entries["entities"], "&amp; &lt; &gt; &quot;")

	def test_newlines_stripped(self):
		"""Literal newlines in definitions are removed."""
		outpath = self._write_sdic(
			[
				("multiline", "line1\nline2\nline3"),
			]
		)
		result = _parse_sdic(outpath)
		entries = dict(result["entries"])
		self.assertEqual(entries["multiline"], "line1line2line3")

	def test_non_ascii_headwords(self):
		"""Non-ASCII headwords are handled correctly."""
		outpath = self._write_sdic(
			[
				("café", "a coffee shop"),
				("naïve", "innocent"),
				("über", "over"),
			]
		)
		result = _parse_sdic(outpath)
		words = [e[0] for e in result["entries"]]
		# All three words should be present
		self.assertEqual(len(words), 3)
		self.assertIn("café", words)
		self.assertIn("naïve", words)
		self.assertIn("über", words)
		# café collates to CAFE, naïve to NAIVE, über to UBER
		# Sort order should be: café, naïve, über
		self.assertEqual(words, ["café", "naïve", "über"])

	def test_duplicate_headwords_merged(self):
		"""Duplicate headwords are merged with separator."""
		outpath = self._write_sdic(
			[
				("word", "definition 1"),
				("word", "definition 2"),
				("word", "definition 3"),
			]
		)
		result = _parse_sdic(outpath)
		self.assertEqual(result["entry_count"], 1)
		entries = dict(result["entries"])
		self.assertIn("definition 1", entries["word"])
		self.assertIn("definition 2", entries["word"])
		self.assertIn("definition 3", entries["word"])

	def test_alternates_ignored(self):
		"""Alternate terms (synonyms) are ignored; only primary used."""
		outpath = self._write_sdic(
			[
				(["color", "colour"], "a visual property"),
				(["hello", "hi", "hey"], "a greeting"),
			]
		)
		result = _parse_sdic(outpath)
		self.assertEqual(result["entry_count"], 2)
		words = [e[0] for e in result["entries"]]
		self.assertIn("color", words)
		self.assertIn("hello", words)
		self.assertNotIn("colour", words)
		self.assertNotIn("hi", words)

	def test_collate_sorting(self):
		"""Entries are sorted by collated key (accent-folded, uppercase)."""
		outpath = self._write_sdic(
			[
				("zebra", "an animal"),
				("apple", "a fruit"),
				("mango", "a tropical fruit"),
			]
		)
		result = _parse_sdic(outpath)
		words = [e[0] for e in result["entries"]]
		self.assertEqual(words, ["apple", "mango", "zebra"])

	def test_default_metadata_no_options(self):
		"""Writer works with zero configuration using built-in defaults."""
		outpath = self._write_sdic(
			[
				("test", "works without options"),
			]
		)
		result = _parse_sdic(outpath)
		self.assertEqual(result["entry_count"], 1)
		# Collate section should be present (non-zero size)
		collate_size = result["morphems_off"] - result["collate_off"]
		self.assertGreater(collate_size, 0)

	def test_section_offsets_consistent(self):
		"""Section offsets are sequential and consistent."""
		outpath = self._write_sdic(
			[
				("a", "1"),
				("b", "2"),
				("c", "3"),
			]
		)
		result = _parse_sdic(outpath)
		self.assertEqual(result["collate_off"], 128)
		self.assertGreater(result["morphems_off"], result["collate_off"])
		self.assertGreater(result["keyboard_off"], result["morphems_off"])
		self.assertGreater(result["sparse_off"], result["keyboard_off"])
		self.assertGreater(result["data_off"], result["sparse_off"])
		self.assertGreaterEqual(
			result["file_size"],
			result["data_off"],
		)

	def test_bookname_in_header(self):
		"""Dictionary name from glossary info appears in header."""
		outpath = self._write_sdic(
			[("test", "def")],
			bookname="My Amazing Dictionary",
		)
		result = _parse_sdic(outpath)
		self.assertEqual(result["name"], "My Amazing Dictionary")

	def test_custom_merge_separator(self):
		"""Custom merge separator is used for duplicates."""
		outpath = self._write_sdic(
			[("word", "def1"), ("word", "def2")],
			merge_separator=" | ",
		)
		result = _parse_sdic(outpath)
		entries = dict(result["entries"])
		self.assertEqual(entries["word"], "def1 | def2")

	def test_many_entries_multiple_blocks(self):
		"""Enough entries to span multiple blocks."""
		n = 200
		input_entries = [(f"word{i:04d}", f"definition number {i}") for i in range(n)]
		outpath = self._write_sdic(input_entries)
		result = _parse_sdic(outpath)
		self.assertEqual(result["entry_count"], n)
		self.assertGreater(len(result["blocks"]), 1)
		# All entries should be present
		self.assertEqual(len(result["entries"]), n)


if __name__ == "__main__":
	unittest.main()
