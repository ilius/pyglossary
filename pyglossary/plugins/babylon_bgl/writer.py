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
from typing import TYPE_CHECKING

from pyglossary.compress import stdCompressions

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
	parts = [
		bytes([len(b_word)]),
		b_word,
		len(b_defi).to_bytes(2, "big"),
		b_defi,
	]
	for b_alt in b_alts:
		parts += (bytes([len(b_alt)]), b_alt)
	return b"".join(parts)


def _pack_entry_type11(b_word: bytes, b_defi: bytes, b_alts: list[bytes]) -> bytes:
	parts = [len(b_word).to_bytes(5, "big"), b_word]
	parts.append(len(b_alts).to_bytes(4, "big"))
	for b_alt in b_alts:
		parts += (len(b_alt).to_bytes(4, "big"), b_alt)
	parts += (len(b_defi).to_bytes(4, "big"), b_defi)
	return b"".join(parts)


def _pack_type2(filename: str, data: bytes) -> bytes:
	b_name = filename.encode("ascii", "replace")
	if len(b_name) > 255:
		b_name = b_name[:255]
	return bytes([len(b_name)]) + b_name + data


def add_t3(gz: gzip.GzipFile, code: int, value: bytes) -> None:
	gz.write(_pack_block(3, _pack_type3(code, value)))


def writeHeader(
	gz: gzip.GzipFile,
	glos: WriterGlossaryType,
) -> None:
	gz.write(_pack_block(0, b"\x08\x42"))

	title = (glos.getInfo("name") or "Glossary").strip() or "Glossary"
	add_t3(gz, 0x01, title.encode("utf-8"))

	add_t3(gz, 0x11, (0x8000).to_bytes(4, "big"))

	add_t3(gz, 0x07, b"\x00\x00\x00\x00")
	add_t3(gz, 0x08, b"\x00\x00\x00\x00")

	add_t3(gz, 0x1A, bytes([0x42]))
	add_t3(gz, 0x1B, bytes([0x42]))

	if glos.getInfo("author"):
		add_t3(gz, 0x02, glos.getInfo("author").encode("utf-8"))
	if glos.getInfo("email"):
		add_t3(gz, 0x03, glos.getInfo("email").encode("utf-8"))
	if glos.getInfo("copyright"):
		add_t3(gz, 0x04, glos.getInfo("copyright").encode("utf-8"))
	desc = glos.getInfo("description")
	if desc:
		add_t3(gz, 0x09, desc.encode("utf-8"))


def writePayload(
	gz: gzip.GzipFile,
	word_entries: list[EntryType],
	data_entries: list[EntryType],
) -> None:

	add_t3(gz, 0x0C, len(word_entries).to_bytes(4, "big"))

	for entry in word_entries:
		terms = entry.l_term
		if not terms:
			continue
		b_word = terms[0].encode("utf-8")
		b_defi = entry.defi.encode("utf-8")
		b_alts = [t.encode("utf-8") for t in terms[1:]]
		if len(b_word) > 255 or any(len(a) > 255 for a in b_alts) or len(b_defi) > 65535:
			gz.write(_pack_block(11, _pack_entry_type11(b_word, b_defi, b_alts)))
		else:
			gz.write(_pack_block(1, _pack_entry_type1(b_word, b_defi, b_alts)))

	for entry in data_entries:
		gz.write(_pack_block(2, _pack_type2(entry.getFileName(), entry.data)))


class Writer:
	compressions = stdCompressions
	_gzip_offset: int = 64

	def __init__(self, glos: WriterGlossaryType) -> None:
		self._glos = glos
		self._filename = ""

	def open(self, filename: str) -> None:
		self._filename = filename

	def finish(self) -> None:
		self._filename = ""

	def write(self) -> Generator[None, EntryType | None, None]:
		word_entries: list[EntryType] = []
		data_entries: list[EntryType] = []
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				data_entries.append(entry)
				continue
			terms = entry.l_term
			if not terms or not str(terms[0]).strip():
				continue
			word_entries.append(entry)

		gzip_offset = self._gzip_offset
		if gzip_offset < 6:
			raise ValueError("gzip_offset must be at least 6")
		glos = self._glos

		with open(self._filename, "wb") as out:
			out.write(b"\x12\x34\x00\x01")
			out.write(gzip_offset.to_bytes(2, "big"))
			padding_len = gzip_offset - 6
			if padding_len:
				out.write(b"\x00" * padding_len)

			with gzip.GzipFile(fileobj=out, mode="wb", mtime=0) as gz:
				writeHeader(gz, glos)
				writePayload(
					gz,
					word_entries,
					data_entries,
				)
