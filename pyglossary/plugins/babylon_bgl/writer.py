# -*- coding: utf-8 -*-
#
# Copyright © 2008-2026 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# This file is part of PyGlossary project, http://github.com/ilius/pyglossary
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.

from __future__ import annotations

import gzip
import io
from typing import TYPE_CHECKING

from pyglossary.compression import stdCompressions

if TYPE_CHECKING:
	from collections.abc import Generator

	from pyglossary.glossary_types import EntryType, WriterGlossaryType

__all__ = ["Writer"]


def _pack_block(block_type: int, payload: bytes) -> bytes:
	L = len(payload)
	if L + 4 <= 0xF:
		return bytes([(L + 4) << 4 | block_type]) + payload
	for nibble in range(4):
		nbytes = nibble + 1
		max_len = (1 << (8 * nbytes)) - 1
		if max_len >= L:
			first = (nibble << 4) | block_type
			return bytes([first]) + L.to_bytes(nbytes, "big") + payload
	msg = f"BGL writer: block payload too large ({L} bytes)"
	raise ValueError(msg)


def _pack_type3(code: int, value: bytes) -> bytes:
	return code.to_bytes(2, "big") + value


def _pack_entry_type1(b_word: bytes, b_defi: bytes, b_alts: list[bytes]) -> bytes:
	if len(b_word) > 255 or any(len(a) > 255 for a in b_alts):
		return _pack_entry_type11(b_word, b_defi, b_alts)
	parts = [bytes([len(b_word)]), b_word]
	parts.append(len(b_defi).to_bytes(2, "big"))
	parts.append(b_defi)
	for b_alt in b_alts:
		parts.append(bytes([len(b_alt)]))
		parts.append(b_alt)
	return b"".join(parts)


def _pack_entry_type11(b_word: bytes, b_defi: bytes, b_alts: list[bytes]) -> bytes:
	parts = [len(b_word).to_bytes(5, "big"), b_word]
	parts.append(len(b_alts).to_bytes(4, "big"))
	for b_alt in b_alts:
		parts.append(len(b_alt).to_bytes(4, "big"))
		parts.append(b_alt)
	parts.append(len(b_defi).to_bytes(4, "big"))
	parts.append(b_defi)
	return b"".join(parts)


def _pack_type2(filename: str, data: bytes) -> bytes:
	b_name = filename.encode("ascii", "replace")
	if len(b_name) > 255:
		b_name = b_name[:255]
	return bytes([len(b_name)]) + b_name + data


def _build_payload(
	glos: WriterGlossaryType,
	word_entries: list[EntryType],
	data_entries: list[EntryType],
) -> bytes:
	chunks: list[bytes] = []

	chunks.append(_pack_block(0, b"\x08\x42"))

	def add_t3(code: int, value: bytes) -> None:
		chunks.append(_pack_block(3, _pack_type3(code, value)))

	title = (glos.getInfo("name") or "Glossary").strip() or "Glossary"
	add_t3(0x01, title.encode("utf-8"))

	add_t3(0x11, (0x8000).to_bytes(4, "big"))

	add_t3(0x07, b"\x00\x00\x00\x00")
	add_t3(0x08, b"\x00\x00\x00\x00")

	add_t3(0x1A, bytes([0x42]))
	add_t3(0x1B, bytes([0x42]))

	if glos.getInfo("author"):
		add_t3(0x02, glos.getInfo("author").encode("utf-8"))
	if glos.getInfo("email"):
		add_t3(0x03, glos.getInfo("email").encode("utf-8"))
	if glos.getInfo("copyright"):
		add_t3(0x04, glos.getInfo("copyright").encode("utf-8"))
	desc = glos.getInfo("description")
	if desc:
		add_t3(0x09, desc.encode("utf-8"))

	add_t3(0x0C, len(word_entries).to_bytes(4, "big"))

	for entry in word_entries:
		terms = entry.l_term
		if not terms:
			continue
		b_word = terms[0].encode("utf-8")
		b_defi = entry.defi.encode("utf-8")
		b_alts = [t.encode("utf-8") for t in terms[1:]]
		entry_payload = _pack_entry_type1(b_word, b_defi, b_alts)
		chunks.append(_pack_block(1, entry_payload))

	for entry in data_entries:
		fname = entry.getFileName()
		chunks.append(_pack_block(2, _pack_type2(fname, entry.data)))

	return b"".join(chunks)


def _write_bgl_file(filename: str, raw_payload: bytes, gzip_offset: int) -> None:
	if gzip_offset < 6:
		raise ValueError("gzip_offset must be at least 6")
	buf = io.BytesIO()
	with gzip.GzipFile(fileobj=buf, mode="wb", mtime=0) as gz:
		gz.write(raw_payload)
	gzip_bytes = buf.getvalue()
	with open(filename, "wb") as out:
		out.write(b"\x12\x34\x00\x01")
		out.write(gzip_offset.to_bytes(2, "big"))
		padding_len = gzip_offset - 6
		if padding_len:
			out.write(b"\x00" * padding_len)
		out.write(gzip_bytes)


class Writer:
	compressions = stdCompressions
	_gzip_offset: int = 64

	def __init__(self, glos: WriterGlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._word_entries: list[EntryType] = []
		self._data_entries: list[EntryType] = []

	def open(self, filename: str) -> None:
		self._filename = filename

	def finish(self) -> None:
		self._filename = ""

	def write(self) -> Generator[None, EntryType | None, None]:
		self._word_entries = []
		self._data_entries = []
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				self._data_entries.append(entry)
				continue
			terms = entry.l_term
			if not terms or not str(terms[0]).strip():
				continue
			self._word_entries.append(entry)

		raw = _build_payload(self._glos, self._word_entries, self._data_entries)
		_write_bgl_file(self._filename, raw, self._gzip_offset)
