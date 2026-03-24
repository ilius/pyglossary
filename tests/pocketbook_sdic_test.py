# -*- coding: utf-8 -*-
"""Unit tests for PocketBook SDIC writer helpers."""

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

from pyglossary.plugins.pocketbook_sdic.writer import (
	BLOCK_TRAILER,
	BODY_PREFIX,
	BODY_SUFFIX,
	DEFAULT_MAX_ENTRY_SIZE,
	FORMAT_VERSION,
	HEADER_SIZE,
	MAX_COMPRESSED_BLOCK_SIZE,
	MAX_RAW_BLOCK_SIZE,
	MAX_WORDS_PER_BLOCK,
	SIGNATURE,
	_build_header,
	_build_sparse_index,
	_encode_entry,
	_pack_blocks,
	_prepare_collate_section,
	_prepare_keyboard_section,
	_prepare_morphems_section,
	_prepare_section_compressed,
	_prepare_sparse_index_section,
	encode_body,
	get_collated_key,
	load_collates,
)


class TestLoadCollates(unittest.TestCase):
	"""Test collates.txt parsing."""

	def _write_collates(self, content: str) -> str:
		fd, path = tempfile.mkstemp(suffix=".txt")
		with os.fdopen(fd, "w", encoding="utf-8") as f:
			f.write(content)
		return path

	def test_basic_mapping(self):
		path = self._write_collates("aàáâ=A\neèéê=E\n")
		try:
			collate = load_collates(path)
		finally:
			os.unlink(path)
		self.assertEqual(collate[ord("a")], ord("A"))
		self.assertEqual(collate[ord("à")], ord("A"))
		self.assertEqual(collate[ord("á")], ord("A"))
		self.assertEqual(collate[ord("e")], ord("E"))
		self.assertEqual(collate[ord("è")], ord("E"))

	def test_strip_behavior(self):
		"""Empty right-hand side maps to None (strip/delete)."""
		path = self._write_collates(".,-_ =\n")
		try:
			collate = load_collates(path)
		finally:
			os.unlink(path)
		self.assertIsNone(collate[ord(".")])
		self.assertIsNone(collate[ord(",")])
		self.assertIsNone(collate[ord("-")])
		self.assertIsNone(collate[ord("_")])
		self.assertIsNone(collate[ord(" ")])

	def test_empty_lines_ignored(self):
		path = self._write_collates("\n\naà=A\n\n")
		try:
			collate = load_collates(path)
		finally:
			os.unlink(path)
		self.assertEqual(len(collate), 2)

	def test_line_without_equals_ignored(self):
		path = self._write_collates("no equals here\naà=A\n")
		try:
			collate = load_collates(path)
		finally:
			os.unlink(path)
		self.assertEqual(len(collate), 2)

	def test_default_collates(self):
		"""Built-in defaults/collates.txt loads without error."""
		defaults_dir = os.path.join(
			dirname(dirname(abspath(__file__))),
			"pyglossary",
			"plugins",
			"pocketbook_sdic",
			"defaults",
		)
		path = os.path.join(defaults_dir, "collates.txt")
		collate = load_collates(path)
		self.assertGreater(len(collate), 50)
		# English collates map 'a' to 'A'
		self.assertEqual(collate[ord("a")], ord("A"))


class TestGetCollatedKey(unittest.TestCase):
	"""Test collated key generation."""

	def setUp(self):
		self.collate: dict[int, int | None] = {
			ord("a"): ord("A"),
			ord("à"): ord("A"),
			ord("á"): ord("A"),
			ord("e"): ord("E"),
			ord("é"): ord("E"),
			ord(" "): None,  # strip
			ord("-"): None,  # strip
		}

	def test_basic_uppercase(self):
		self.assertEqual(get_collated_key("hello", self.collate), "HELLO")

	def test_accent_folding(self):
		self.assertEqual(get_collated_key("café", self.collate), "CAFE")

	def test_strip_characters(self):
		self.assertEqual(
			get_collated_key("ice-cream", self.collate),
			"ICECREAM",
		)
		self.assertEqual(
			get_collated_key("hello world", self.collate),
			"HELLOWORLD",
		)

	def test_unmapped_characters_pass_through(self):
		"""Characters not in collate map pass through and get uppercased."""
		self.assertEqual(get_collated_key("xyz", self.collate), "XYZ")

	def test_empty_string(self):
		self.assertEqual(get_collated_key("", self.collate), "")


class TestEncodeBody(unittest.TestCase):
	"""Test definition body encoding."""

	def test_simple_text(self):
		self.assertEqual(encode_body("hello world"), b"hello world")

	def test_newlines_removed(self):
		self.assertEqual(
			encode_body("line1\nline2\nline3"),
			b"line1line2line3",
		)

	def test_indentation_stripped(self):
		self.assertEqual(
			encode_body("  indented\n\ttabbed"),
			b"indentedtabbed",
		)

	def test_html_tags_preserved(self):
		self.assertEqual(
			encode_body("<b>bold</b> and <i>italic</i>"),
			b"<b>bold</b> and <i>italic</i>",
		)

	def test_html_entities_preserved(self):
		self.assertEqual(
			encode_body("&amp; &lt; &gt; &quot;"),
			b"&amp; &lt; &gt; &quot;",
		)

	def test_br_tags_preserved(self):
		self.assertEqual(
			encode_body("line1<br>line2<br/>line3"),
			b"line1<br>line2<br/>line3",
		)

	def test_mixed_html_and_newlines(self):
		self.assertEqual(
			encode_body("<b>bold</b>\n  <i>italic</i>"),
			b"<b>bold</b><i>italic</i>",
		)


class TestEncodeEntry(unittest.TestCase):
	"""Test SDIC entry payload encoding."""

	def test_basic_entry(self):
		payload = _encode_entry("hello", b"world")
		size = struct.unpack_from("<H", payload, 0)[0]
		self.assertEqual(size, len(payload))
		# word + NUL
		nul = payload.index(0, 2)
		word = payload[2:nul].decode("utf-8")
		self.assertEqual(word, "hello")
		# body markers
		body_start = nul + 1
		self.assertEqual(payload[body_start : body_start + 1], BODY_PREFIX)
		self.assertEqual(payload[-3:], BODY_SUFFIX)

	def test_utf8_word(self):
		payload = _encode_entry("café", b"definition")
		nul = payload.index(0, 2)
		word = payload[2:nul].decode("utf-8")
		self.assertEqual(word, "café")


class TestPackBlocks(unittest.TestCase):
	"""Test block packing algorithm."""

	def test_single_small_entry(self):
		payloads = [b"small entry data"]
		blocks, counts, _max_size, widened = _pack_blocks(payloads)
		self.assertEqual(len(blocks), 1)
		self.assertEqual(counts, [1])
		self.assertEqual(widened, 0)
		# Verify block decompresses correctly
		raw = zlib.decompress(blocks[0])
		self.assertTrue(raw.endswith(BLOCK_TRAILER))
		self.assertEqual(raw[:-2], b"small entry data")

	def test_multiple_small_entries_pack_together(self):
		payloads = [b"entry" + bytes([i]) for i in range(10)]
		blocks, counts, _max_size, widened = _pack_blocks(payloads)
		self.assertEqual(len(blocks), 1)
		self.assertEqual(counts, [10])
		self.assertEqual(widened, 0)

	def test_max_100_entries_per_block(self):
		payloads = [b"x" for _ in range(150)]
		_blocks, counts, _max_size, _widened = _pack_blocks(payloads)
		self.assertEqual(sum(counts), 150)
		for c in counts:
			self.assertLessEqual(c, MAX_WORDS_PER_BLOCK)

	def test_raw_size_limit_enforced(self):
		# Each entry is ~700 bytes; 100 of them > 65531
		payloads = [b"x" * 700 for _ in range(100)]
		blocks, _counts, _max_size, _widened = _pack_blocks(payloads)
		self.assertGreater(len(blocks), 1)
		for block in blocks:
			raw = zlib.decompress(block)
			self.assertLess(len(raw), MAX_RAW_BLOCK_SIZE)

	def test_widened_single_entry_fallback(self):
		# A single large entry that compresses to > 4097 but < 65535.
		# Use pseudo-random data that doesn't compress well.
		import random

		rng = random.Random(42)
		big = bytes(rng.getrandbits(8) for _ in range(30000))
		payloads = [big]
		blocks, counts, _max_size, widened = _pack_blocks(payloads)
		self.assertEqual(len(blocks), 1)
		self.assertEqual(counts, [1])
		self.assertEqual(widened, 1)
		compressed_size = len(blocks[0])
		self.assertGreater(compressed_size, MAX_COMPRESSED_BLOCK_SIZE)
		self.assertLessEqual(compressed_size, 0xFFFF)

	def test_oversized_entry_raises(self):
		# An entry so large even compression won't bring it under 65535.
		import random

		rng = random.Random(99)
		huge = bytes(rng.getrandbits(8) for _ in range(200000))
		payloads = [huge]
		with self.assertRaises(ValueError):
			_pack_blocks(payloads)


class TestBuildSparseIndex(unittest.TestCase):
	"""Test sparse index construction."""

	def test_single_block(self):
		words = ["alpha", "beta", "gamma"]
		blocks = [b"compressed"]
		counts = [3]
		raw = _build_sparse_index(words, blocks, counts)
		# Should be: uint16(10) + "alpha\0"
		size = struct.unpack_from("<H", raw, 0)[0]
		self.assertEqual(size, len(blocks[0]))
		nul = raw.index(0, 2)
		first_word = raw[2:nul].decode("utf-8")
		self.assertEqual(first_word, "alpha")

	def test_multiple_blocks(self):
		words = ["alpha", "beta", "gamma", "delta"]
		blocks = [b"block0", b"block1"]
		counts = [2, 2]
		raw = _build_sparse_index(words, blocks, counts)
		# First entry: block0, first word = "alpha"
		off = 0
		s1 = struct.unpack_from("<H", raw, off)[0]
		self.assertEqual(s1, len(blocks[0]))
		off += 2
		nul = raw.index(0, off)
		self.assertEqual(raw[off:nul].decode("utf-8"), "alpha")
		off = nul + 1
		# Second entry: block1, first word = "gamma"
		s2 = struct.unpack_from("<H", raw, off)[0]
		self.assertEqual(s2, len(blocks[1]))
		off += 2
		nul = raw.index(0, off)
		self.assertEqual(raw[off:nul].decode("utf-8"), "gamma")


class TestPrepareSections(unittest.TestCase):
	"""Test section encoding."""

	def test_collate_section_encoding(self):
		collate = {ord("a"): ord("A"), ord("b"): ord("B")}
		section = _prepare_collate_section(collate)
		byte_len = struct.unpack_from("<I", section, 0)[0]
		self.assertEqual(byte_len, 8)  # 2 pairs * 4 bytes
		# Pairs should be sorted by key
		k1 = struct.unpack_from("<H", section, 4)[0]
		v1 = struct.unpack_from("<H", section, 6)[0]
		k2 = struct.unpack_from("<H", section, 8)[0]
		v2 = struct.unpack_from("<H", section, 10)[0]
		self.assertEqual(chr(k1), "a")
		self.assertEqual(chr(v1), "A")
		self.assertEqual(chr(k2), "b")
		self.assertEqual(chr(v2), "B")

	def test_collate_section_sorted(self):
		"""Pairs must be sorted by key for deterministic output."""
		collate = {ord("z"): ord("Z"), ord("a"): ord("A")}
		section = _prepare_collate_section(collate)
		k1 = struct.unpack_from("<H", section, 4)[0]
		k2 = struct.unpack_from("<H", section, 8)[0]
		self.assertLess(k1, k2)

	def test_keyboard_section_compressed(self):
		keyboard = "EN: English\nqwertyuio"
		section = _prepare_keyboard_section(keyboard)
		size = struct.unpack_from("<I", section, 0)[0]
		decompressed = zlib.decompress(section[4:])
		self.assertEqual(len(decompressed), size)
		self.assertEqual(decompressed.decode("utf-8"), keyboard)

	def test_keyboard_too_large_raises(self):
		with self.assertRaises(ValueError):
			_prepare_keyboard_section("x" * 4096)

	def test_morphems_section(self):
		morphems = ";comment\n%1=aeiou\n^?es=.e/."
		collate: dict[int, int] = {ord("a"): ord("A")}
		section = _prepare_morphems_section(morphems, collate)
		size = struct.unpack_from("<I", section, 0)[0]
		decompressed = zlib.decompress(section[4:])
		self.assertEqual(len(decompressed), size)
		# Should contain UTF-16LE encoded data
		# The comment line should be skipped
		# Content should be processed through GetCollatedKey

	def test_morphems_skips_comments_and_blanks(self):
		morphems = ";this is a comment\n\n%1=aeiou"
		collate: dict[int, int] = {}
		section = _prepare_morphems_section(morphems, collate)
		_size = struct.unpack_from("<I", section, 0)[0]
		decompressed = zlib.decompress(section[4:])
		# Only "%1=AEIOU" should remain (uppercased by GetCollatedKey)
		# Each char as uint16 LE + NUL separator + final NUL
		# The output should have only 1 non-empty line processed
		runes = [
			struct.unpack_from("<H", decompressed, i)[0]
			for i in range(0, len(decompressed), 2)
		]
		# Find the content between NUL separators
		content = "".join(chr(r) for r in runes if r != 0)
		self.assertIn("%1=AEIOU", content)

	def test_sparse_index_section_compressed(self):
		raw_index = b"\x0a\x00hello\x00"
		section = _prepare_sparse_index_section(raw_index)
		size = struct.unpack_from("<I", section, 0)[0]
		self.assertEqual(size, len(raw_index) + 2)  # +2 for trailer
		decompressed = zlib.decompress(section[4:])
		self.assertEqual(len(decompressed), size)
		self.assertTrue(decompressed.endswith(b"\x00\x00"))


class TestBuildHeader(unittest.TestCase):
	"""Test header construction."""

	def test_header_size(self):
		header = _build_header(
			entry_count=100,
			max_entry_size=500,
			name="Test",
			section_sizes=[10, 20, 30, 40],
		)
		self.assertEqual(len(header), HEADER_SIZE)

	def test_header_signature(self):
		header = _build_header(0, 0, "", [0, 0, 0, 0])
		self.assertEqual(header[:4], SIGNATURE)

	def test_header_version(self):
		header = _build_header(0, 0, "", [0, 0, 0, 0])
		version = struct.unpack_from("<I", header, 4)[0]
		self.assertEqual(version, FORMAT_VERSION)

	def test_header_entry_count(self):
		header = _build_header(42, 0, "", [0, 0, 0, 0])
		count = struct.unpack_from("<I", header, 8)[0]
		self.assertEqual(count, 42)

	def test_header_max_entry_size_default(self):
		header = _build_header(0, 100, "", [0, 0, 0, 0])
		max_size = struct.unpack_from("<I", header, 0x0C)[0]
		self.assertEqual(max_size, DEFAULT_MAX_ENTRY_SIZE)

	def test_header_max_entry_size_large(self):
		header = _build_header(0, 100000, "", [0, 0, 0, 0])
		max_size = struct.unpack_from("<I", header, 0x0C)[0]
		self.assertEqual(max_size, 100000)

	def test_header_section_offsets(self):
		section_sizes = [100, 200, 300, 400]
		header = _build_header(0, 0, "", section_sizes)
		collate_off = struct.unpack_from("<I", header, 0x24)[0]
		morphems_off = struct.unpack_from("<I", header, 0x28)[0]
		keyboard_off = struct.unpack_from("<I", header, 0x2C)[0]
		sparse_off = struct.unpack_from("<I", header, 0x38)[0]
		data_off = struct.unpack_from("<I", header, 0x3C)[0]

		self.assertEqual(collate_off, HEADER_SIZE)
		self.assertEqual(morphems_off, HEADER_SIZE + 100)
		self.assertEqual(keyboard_off, HEADER_SIZE + 300)
		self.assertEqual(sparse_off, HEADER_SIZE + 600)
		self.assertEqual(data_off, HEADER_SIZE + 1000)

	def test_header_name(self):
		header = _build_header(0, 0, "My Dictionary", [0, 0, 0, 0])
		name = header[0x40:0x80].split(b"\x00")[0]
		self.assertEqual(name, b"My Dictionary")

	def test_header_name_truncated(self):
		long_name = "A" * 100
		header = _build_header(0, 0, long_name, [0, 0, 0, 0])
		# Name field is 64 bytes
		name_bytes = header[0x40:0x80]
		self.assertEqual(len(name_bytes), 64)

	def test_header_reserved_fields_zero(self):
		header = _build_header(0, 0, "", [0, 0, 0, 0])
		# Reserved1 at 0x10-0x23 (encryption seed, metadata offset)
		for i in range(0x10, 0x24):
			self.assertEqual(
				header[i],
				0,
				f"byte at offset {i:#x} should be 0",
			)
		# Reserved2 at 0x30-0x37 (DRM)
		for i in range(0x30, 0x38):
			self.assertEqual(
				header[i],
				0,
				f"byte at offset {i:#x} should be 0",
			)


class TestSectionCompressed(unittest.TestCase):
	"""Test generic section compression helper."""

	def test_round_trip(self):
		data = b"test data for compression"
		section = _prepare_section_compressed(data)
		size = struct.unpack_from("<I", section, 0)[0]
		self.assertEqual(size, len(data))
		decompressed = zlib.decompress(section[4:])
		self.assertEqual(decompressed, data)


if __name__ == "__main__":
	unittest.main()
