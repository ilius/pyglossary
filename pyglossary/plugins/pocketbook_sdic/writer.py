# -*- coding: utf-8 -*-
from __future__ import annotations

import os
import struct
import zlib
from typing import TYPE_CHECKING

from pyglossary.core import log

if TYPE_CHECKING:
	from collections.abc import Generator

	from pyglossary.glossary_types import EntryType, WriterGlossaryType

__all__ = ["Writer"]

# SDIC format constants
SIGNATURE = b"SDIC"
FORMAT_VERSION = 0x101
HEADER_SIZE = 128
MAX_NAME_SIZE = 64
DEFAULT_MAX_ENTRY_SIZE = 0xFFFC  # 65532

# Block packing limits
MAX_WORDS_PER_BLOCK = 100
MAX_RAW_BLOCK_SIZE = 65531
MAX_COMPRESSED_BLOCK_SIZE = 4097

# Entry body markers
BODY_PREFIX = b"\x20"
BODY_SUFFIX = b"\x20\x0a\x00"
BLOCK_TRAILER = b"\x00\x00"


def load_collates(path: str) -> dict[int, int]:
	"""
	Parse collates.txt into a mapping of codepoint -> canonical codepoint.

	Each line has the form ``chars=C`` where every character before the
	last ``=`` maps to the first character after ``=``.  An empty
	right-hand side means *strip* (map to 0).
	"""
	collate: dict[int, int] = {}
	with open(path, encoding="utf-8") as f:
		for line in f:
			line = line.rstrip("\r\n")
			if not line:
				continue
			eq_idx = line.rfind("=")
			if eq_idx < 0:
				continue
			right = line[eq_idx + 1 :]
			canonical = ord(right[0]) if right else 0
			for ch in line[:eq_idx]:
				collate[ord(ch)] = canonical
	return collate


def get_collated_key(word: str, collate: dict[int, int]) -> str:
	"""Return the collated, uppercased form of *word*."""
	buf: list[str] = []
	for ch in word:
		cp = ord(ch)
		replacement = collate.get(cp)
		if replacement is not None:
			if replacement != 0:
				buf.append(chr(replacement))
			# else: strip
		else:
			buf.append(ch)
	return "".join(buf).upper()


def _compare_collated(
	a: str,
	b: str,
	collate: dict[int, int],
) -> int:
	"""Compare two words under collation, with raw tiebreak."""
	ia = 0
	ib = 0
	la = len(a)
	lb = len(b)
	while True:
		# advance a past stripped runes
		ra = 0
		while ia < la:
			cp = ord(a[ia])
			ia += 1
			repl = collate.get(cp)
			if repl is not None:
				cp = repl
			if cp != 0:
				ra = cp
				break
		# advance b past stripped runes
		rb = 0
		while ib < lb:
			cp = ord(b[ib])
			ib += 1
			repl = collate.get(cp)
			if repl is not None:
				cp = repl
			if cp != 0:
				rb = cp
				break
		# uppercase
		chra = chr(ra).upper() if ra else ""
		chrb = chr(rb).upper() if rb else ""
		if chra != chrb:
			return (chra > chrb) - (chra < chrb)
		if ra == 0:
			return 0


def encode_body(text: str) -> bytes:
	"""
	Encode a definition body for SDIC.

	Strips leading whitespace from each line, removes literal newlines,
	and preserves HTML tags and entities verbatim.
	"""
	parts: list[str] = []
	for line in text.split("\n"):
		parts.append(line.lstrip(" \t"))
	return "".join(parts).encode("utf-8")


def _encode_entry(word: str, body_bytes: bytes) -> bytes:
	r"""
	Encode a single SDIC entry payload.

	Returns: [uint16 total_size][word\\0][0x20][body][0x20 0x0A 0x00]
	"""
	key = word.encode("utf-8") + b"\x00"
	payload = key + BODY_PREFIX + body_bytes + BODY_SUFFIX
	total_size = 2 + len(payload)
	return struct.pack("<H", total_size) + payload


def _zlib_compress(data: bytes) -> bytes:
	"""Compress data with zlib at best compression level."""
	compress = zlib.compressobj(9, zlib.DEFLATED, zlib.MAX_WBITS)
	result = compress.compress(data)
	result += compress.flush()
	return result


def _pack_blocks(
	payloads: list[bytes],
) -> tuple[list[bytes], list[int], int, int]:
	"""
	Pack entry payloads into compressed blocks using binary search.

	Returns (blocks, counts, max_block_size, widened_count).
	"""
	total = len(payloads)
	blocks: list[bytes] = []
	counts: list[int] = []
	max_block_size = 0
	widened_count = 0

	start = 0
	while start < total:
		lo = 1
		hi = min(MAX_WORDS_PER_BLOCK, total - start)
		best_block: bytes | None = None
		best_count = 0

		while lo <= hi:
			mid = (lo + hi) // 2

			raw = b"".join(payloads[start : start + mid]) + BLOCK_TRAILER
			if len(raw) >= MAX_RAW_BLOCK_SIZE:
				hi = mid - 1
				continue

			blob = _zlib_compress(raw)
			if len(blob) < MAX_COMPRESSED_BLOCK_SIZE:
				best_block = blob
				best_count = mid
				lo = mid + 1
			else:
				hi = mid - 1

		if best_block is None:
			# Single-entry fallback with relaxed ceiling
			raw = payloads[start] + BLOCK_TRAILER
			blob = _zlib_compress(raw)
			if len(blob) > 0xFFFF:
				raise ValueError(
					f"entry at index {start} is too large: "
					f"{len(payloads[start])} bytes raw, "
					f"compresses to {len(blob)} bytes "
					f"(block limit: 65535)",
				)
			best_block = blob
			best_count = 1
			widened_count += 1

		max_block_size = max(max_block_size, len(best_block))

		blocks.append(best_block)
		counts.append(best_count)
		start += best_count

	return blocks, counts, max_block_size, widened_count


def _build_sparse_index(
	words: list[str],
	blocks: list[bytes],
	counts: list[int],
) -> bytes:
	r"""Build the raw sparse index: [uint16 size][first_word\\0] per block."""
	parts: list[bytes] = []
	entry_start = 0
	for i, block in enumerate(blocks):
		first_word = words[entry_start].encode("utf-8") + b"\x00"
		entry = struct.pack("<H", len(block)) + first_word
		parts.append(entry)
		entry_start += counts[i]
	return b"".join(parts)


def _prepare_section_compressed(data: bytes) -> bytes:
	"""Wrap *data* in a compressed section: [uint32 size][zlib data]."""
	size_prefix = struct.pack("<I", len(data))
	return size_prefix + _zlib_compress(data)


def _prepare_collate_section(collate: dict[int, int]) -> bytes:
	"""Build the collate section: [uint32 byte-length][pairs...]."""
	pairs = sorted(collate.items())
	num_bytes = len(pairs) * 4
	buf = struct.pack("<I", num_bytes)
	for k, v in pairs:
		buf += struct.pack("<HH", k, v)
	return buf


def _prepare_morphems_section(
	morphems: str,
	collate: dict[int, int],
) -> bytes:
	"""Build the morphems section (UTF-16LE, zlib-compressed)."""
	output: list[int] = []
	for line in morphems.split("\n"):
		line = line.strip()
		if not line or line.startswith(";"):
			continue
		processed = get_collated_key(line, collate)
		for ch in processed:
			output.append(ord(ch))
		output.append(0)  # NUL terminator
	output.append(0)  # final sentinel

	body = b""
	for cp in output:
		body += struct.pack("<H", cp)

	return _prepare_section_compressed(body)


def _prepare_keyboard_section(keyboard: str) -> bytes:
	"""Build the keyboard section (UTF-8, zlib-compressed)."""
	if len(keyboard) >= 4096:
		raise ValueError("keyboard file is too large (>= 4096 bytes)")
	return _prepare_section_compressed(keyboard.encode("utf-8"))


def _prepare_sparse_index_section(sparse_index: bytes) -> bytes:
	"""
	Build the sparse index section (zlib-compressed).

	The uncompressed size includes the 2-byte trailer.
	"""
	uncompressed_size = len(sparse_index) + 2
	size_prefix = struct.pack("<I", uncompressed_size)
	return size_prefix + _zlib_compress(sparse_index + b"\x00\x00")


def _build_header(
	entry_count: int,
	max_entry_size: int,
	name: str,
	section_sizes: list[int],
) -> bytes:
	"""Build the 128-byte SDIC header."""
	header = bytearray(HEADER_SIZE)
	# Signature (0x00)
	header[0x00:0x04] = SIGNATURE
	# Version (0x04)
	struct.pack_into("<I", header, 0x04, FORMAT_VERSION)
	# EntryCount (0x08)
	struct.pack_into("<I", header, 0x08, entry_count)
	# MaxEntrySize (0x0C)
	struct.pack_into("<I", header, 0x0C, max(DEFAULT_MAX_ENTRY_SIZE, max_entry_size))
	# Reserved1 (0x10-0x23) stays zero — no encryption, no metadata

	# Section offsets
	offset = HEADER_SIZE
	# CollateOffset (0x24)
	struct.pack_into("<I", header, 0x24, offset)
	offset += section_sizes[0]
	# MorphemsOffset (0x28)
	struct.pack_into("<I", header, 0x28, offset)
	offset += section_sizes[1]
	# KeyboardOffset (0x2C)
	struct.pack_into("<I", header, 0x2C, offset)
	offset += section_sizes[2]
	# Reserved2 (0x30-0x37) stays zero — no DRM
	# SparseIndexOffset (0x38)
	struct.pack_into("<I", header, 0x38, offset)
	offset += section_sizes[3]
	# FirstDataBlockOffset (0x3C)
	struct.pack_into("<I", header, 0x3C, offset)

	# Name (0x40, 64 bytes, null-padded)
	name_bytes = name.encode("utf-8")[:MAX_NAME_SIZE]
	header[0x40 : 0x40 + len(name_bytes)] = name_bytes

	return bytes(header)


def _resolve_metadata_file(
	explicit_path: str | None,
	metadata_dir: str | None,
	filename: str,
	defaults_dir: str,
) -> str:
	"""Resolve a metadata file path using the fallback chain."""
	if explicit_path:
		if not os.path.isfile(explicit_path):
			raise FileNotFoundError(
				f"Explicit metadata file not found: {explicit_path}",
			)
		return explicit_path
	if metadata_dir:
		path = os.path.join(metadata_dir, filename)
		if os.path.isfile(path):
			return path
		raise FileNotFoundError(
			f"{filename} not found in metadata_dir: {metadata_dir}",
		)
	# Built-in defaults
	return os.path.join(defaults_dir, filename)


class Writer:
	_metadata_dir: str = ""
	_collates_path: str = ""
	_keyboard_path: str = ""
	_morphems_path: str = ""
	_merge_separator: str = "<br>"

	def __init__(self, glos: WriterGlossaryType) -> None:
		self._glos = glos
		self._filename = ""

	def open(self, filename: str) -> None:
		self._filename = filename

	def finish(self) -> None:
		self._filename = ""

	def write(self) -> Generator[None, EntryType, None]:
		defaults_dir = os.path.join(
			os.path.dirname(__file__),
			"defaults",
		)
		metadata_dir = self._metadata_dir or None
		collates_path = _resolve_metadata_file(
			self._collates_path or None,
			metadata_dir,
			"collates.txt",
			defaults_dir,
		)
		morphems_path = _resolve_metadata_file(
			self._morphems_path or None,
			metadata_dir,
			"morphems.txt",
			defaults_dir,
		)
		keyboard_path = _resolve_metadata_file(
			self._keyboard_path or None,
			metadata_dir,
			"keyboard.txt",
			defaults_dir,
		)

		collate = load_collates(collates_path)
		with open(morphems_path, encoding="utf-8") as f:
			morphems = f.read().strip()
		with open(keyboard_path, encoding="utf-8") as f:
			keyboard = f.read().strip()

		# Collect entries
		entries: list[tuple[str, str]] = []
		data_count = 0
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				data_count += 1
				continue
			word = entry.l_term[0] if entry.l_term else entry.s_term
			defi = entry.defi
			entries.append((word, defi))

		if data_count > 0:
			log.warning(
				f"Skipped {data_count} binary resource"
				f" entr{'ies' if data_count != 1 else 'y'}"
				f" (not supported by SDIC format)",
			)

		if not entries:
			log.warning("No entries to write")
			return

		# Sort by collated key, then raw word for determinism
		entries.sort(
			key=lambda e: (get_collated_key(e[0], collate), e[0]),
		)

		# Merge duplicate headwords
		merged: list[tuple[str, str]] = [entries[0]]
		sep = self._merge_separator
		for i in range(1, len(entries)):
			word, defi = entries[i]
			if word == merged[-1][0]:
				merged[-1] = (word, merged[-1][1] + sep + defi)
			else:
				merged.append((word, defi))
		entries = merged

		# Encode entries
		words: list[str] = []
		payloads: list[bytes] = []
		max_entry_size = 0
		for word, defi in entries:
			body_bytes = encode_body(defi)
			payload = _encode_entry(word, body_bytes)
			max_entry_size = max(max_entry_size, len(payload))
			words.append(word)
			payloads.append(payload)

		# Pack into compressed blocks
		blocks, counts, _max_block_size, widened_count = _pack_blocks(
			payloads,
		)
		if widened_count > 0:
			log.info(
				f"SDIC: {widened_count} block(s) exceeded default compressed size limit",
			)

		# Build sections
		sparse_index_raw = _build_sparse_index(words, blocks, counts)
		collate_section = _prepare_collate_section(collate)
		morphems_section = _prepare_morphems_section(morphems, collate)
		keyboard_section = _prepare_keyboard_section(keyboard)
		sparse_index_section = _prepare_sparse_index_section(
			sparse_index_raw,
		)

		section_sizes = [
			len(collate_section),
			len(morphems_section),
			len(keyboard_section),
			len(sparse_index_section),
		]

		# Dictionary display name
		name = (
			self._glos.getInfo("bookname")
			or self._glos.getInfo("name")
			or self._glos.getInfo("description")
			or "Dictionary"
		)

		header = _build_header(
			entry_count=len(entries),
			max_entry_size=max_entry_size,
			name=name,
			section_sizes=section_sizes,
		)

		# Write the final file
		with open(self._filename, "wb") as f:
			f.write(header)
			f.write(collate_section)
			f.write(morphems_section)
			f.write(keyboard_section)
			f.write(sparse_index_section)
			f.writelines(blocks)

		log.info(
			f"SDIC: wrote {len(entries)} entries"
			f" in {len(blocks)} blocks to {self._filename}",
		)
