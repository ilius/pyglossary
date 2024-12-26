# -*- coding: utf-8 -*-
from __future__ import annotations

import gzip
import io
import math
import struct
from typing import IO, TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
	from collections.abc import Callable
	from typing import Any

	from .commons import EntryIndexTuple, IndexEntryType

from pyglossary.plugin_lib import mutf8

from .commons import (
	HASH_SET_CAPACITY_FACTOR,
	HASH_SET_INIT,
	HASH_SET_INIT2,
	LINKED_HASH_SET_INIT,
)

__all__ = [
	"write_entry_html",
	"write_entry_index",
	"write_entry_pairs",
	"write_entry_source",
	"write_entry_text",
	"write_int",
	"write_list",
	"write_long",
	"write_string",
]


def write_int(fp: IO[bytes], val: int) -> int:
	return fp.write(struct.pack(">i", val))


def write_byte(fp: IO[bytes], val: int) -> int:
	return fp.write(struct.pack(">b", val))


def write_bool(fp: IO[bytes], val: int) -> int:
	return write_byte(fp, val)


def write_short(fp: IO[bytes], val: int) -> int:
	return fp.write(struct.pack(">h", val))


def write_long(fp: IO[bytes], val: int) -> int:
	return fp.write(struct.pack(">q", val))


def write_float(fp: IO[bytes], val: float) -> int:
	return fp.write(struct.pack(">f", val))


def write_string(fp: IO[bytes], val: str) -> int:
	b_string = mutf8.encode_modified_utf8(val)
	return write_short(fp, len(b_string)) + fp.write(b_string)


def write_hashset(
	fp: IO[bytes],
	data: list[str],
	linked_hash_set: bool = False,
) -> int:
	write_start_offset = fp.tell()
	if linked_hash_set:
		fp.write(LINKED_HASH_SET_INIT)
	else:
		fp.write(HASH_SET_INIT + HASH_SET_INIT2)
	num_entries = len(data)
	capacity = (
		2 ** math.ceil(math.log2(num_entries / HASH_SET_CAPACITY_FACTOR))
		if num_entries > 0
		else 128
	)
	write_int(fp, capacity)
	write_float(fp, HASH_SET_CAPACITY_FACTOR)
	write_int(fp, num_entries)
	for string in data:
		write_byte(fp, 0x74)
		write_string(fp, string)
	write_byte(fp, 0x78)
	return fp.tell() - write_start_offset


T = TypeVar("T")


def write_list(
	fp: IO[bytes],
	fun: Callable[[IO[bytes], T], Any],
	entries: list[T],
) -> int:
	write_start_offset = fp.tell()
	size = len(entries)
	write_int(fp, size)
	toc_offset = fp.tell()
	fp.seek(toc_offset + 8 * (size + 1))
	toc = [fp.tell()]
	for e in entries:
		fun(fp, e)
		toc.append(fp.tell())
	fp.seek(toc_offset)
	fp.write(struct.pack(f">{size + 1}q", *toc))
	fp.seek(toc[-1])
	return fp.tell() - write_start_offset


def write_entry_int(fp: IO[bytes], entry: int) -> int:
	return write_int(fp, entry)


def write_entry_source(fp: IO[bytes], entry: tuple[str, int]) -> int:
	name, count = entry
	return write_string(fp, name) + write_int(fp, count)


def write_entry_pairs(
	fp: IO[bytes],
	entry: tuple[int, list[tuple[str, str]]],
) -> int:
	write_start_offset = fp.tell()
	src_idx, pairs = entry
	write_short(fp, src_idx)
	write_int(fp, len(pairs))
	for p in pairs:
		write_string(fp, p[0])
		write_string(fp, p[1])
	return fp.tell() - write_start_offset


def write_entry_text(fp: IO[bytes], entry: tuple[int, str]) -> int:
	src_idx, txt = entry
	return write_short(fp, src_idx) + write_string(fp, txt)


def write_entry_html(fp: IO[bytes], entry: tuple[int, str, str]) -> int:
	write_start_offset = fp.tell()
	src_idx, title, html = entry
	b_html = "".join(c if ord(c) < 128 else f"&#{ord(c)};" for c in html).encode()
	ib_compr = io.BytesIO()
	with gzip.GzipFile(fileobj=ib_compr, mode="wb", mtime=0) as zf:
		# note that the compressed bytes might differ from the original Java
		# implementation that uses GZIPOutputStream
		zf.write(b_html)
	ib_compr.seek(0)
	b_compr = ib_compr.read()
	write_short(fp, src_idx)
	write_string(fp, title)
	write_int(fp, len(b_html))
	write_int(fp, len(b_compr))
	fp.write(b_compr)
	return fp.tell() - write_start_offset


def write_entry_index(
	fp: IO[bytes],
	entry: EntryIndexTuple,
) -> int:
	write_start_offset = fp.tell()
	(
		short_name,
		long_name,
		iso,
		normalizer_rules,
		swap_flag,
		main_token_count,
		index_entries,
		stop_list,
		rows,
	) = entry
	write_string(fp, short_name)
	write_string(fp, long_name)
	write_string(fp, iso)
	write_string(fp, normalizer_rules)
	write_bool(fp, swap_flag)
	write_int(fp, main_token_count)
	write_list(fp, write_entry_indexentry, index_entries)

	stop_list_size_offset = fp.tell()
	stop_list_offset = stop_list_size_offset + write_int(fp, 0)
	stop_list_size = write_hashset(fp, stop_list, linked_hash_set=True)
	fp.seek(stop_list_size_offset)
	write_int(fp, stop_list_size)
	fp.seek(stop_list_offset + stop_list_size)

	write_int(fp, len(rows))
	write_int(fp, 5)
	row_data = b"".join([struct.pack(">bi", t, i) for t, i in rows])
	fp.write(row_data)
	return fp.tell() - write_start_offset


def write_entry_indexentry(
	fp: IO[bytes],
	entry: IndexEntryType,
) -> None:
	token, start_index, count, token_norm, html_indices = entry
	has_normalized = bool(token_norm)
	write_string(fp, token)
	write_int(fp, start_index)
	write_int(fp, count)
	write_bool(fp, has_normalized)
	if has_normalized:
		write_string(fp, token_norm)
	write_list(fp, write_entry_int, html_indices)
