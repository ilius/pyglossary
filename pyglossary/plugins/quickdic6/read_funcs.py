# -*- coding: utf-8 -*-
from __future__ import annotations

import gzip
import io
import struct
from typing import IO, TYPE_CHECKING, TypeVar

if TYPE_CHECKING:
	from collections.abc import Callable

	from .commons import EntryIndexTuple, IndexEntryType


from pyglossary.plugin_lib import mutf8

from .commons import (
	HASH_SET_CAPACITY_FACTOR,
	HASH_SET_INIT,
	HASH_SET_INIT2,
	LINKED_HASH_SET_INIT,
)

__all__ = [
	"read_entry_html",
	"read_entry_index",
	"read_entry_pairs",
	"read_entry_source",
	"read_entry_text",
	"read_int",
	"read_list",
	"read_long",
	"read_string",
]


def read_byte(fp: IO[bytes]) -> int:
	return struct.unpack(">b", fp.read(1))[0]


def read_bool(fp: IO[bytes]) -> bool:
	return bool(read_byte(fp))


def read_short(fp: IO[bytes]) -> int:
	return struct.unpack(">h", fp.read(2))[0]


def read_int(fp: IO[bytes]) -> int:
	return struct.unpack(">i", fp.read(4))[0]


def read_long(fp: IO[bytes]) -> int:
	return struct.unpack(">q", fp.read(8))[0]


def read_float(fp: IO[bytes]) -> float:
	return struct.unpack(">f", fp.read(4))[0]


def read_string(fp: IO[bytes]) -> str:
	length = read_short(fp)
	return mutf8.decode_modified_utf8(fp.read(length))


def read_hashset(fp: IO[bytes]) -> list[str]:
	hash_set_init = fp.read(len(HASH_SET_INIT))
	if hash_set_init == HASH_SET_INIT:
		hash_set_init2 = fp.read(len(HASH_SET_INIT2))
		assert hash_set_init2 == HASH_SET_INIT2
	else:
		n_extra = len(LINKED_HASH_SET_INIT) - len(HASH_SET_INIT)
		hash_set_init += fp.read(n_extra)
		assert hash_set_init == LINKED_HASH_SET_INIT
	read_int(fp)  # capacity
	capacity_factor = read_float(fp)
	assert capacity_factor == HASH_SET_CAPACITY_FACTOR
	num_entries = read_int(fp)
	data: list[str] = []
	while len(data) < num_entries:
		assert read_byte(fp) == 0x74
		data.append(read_string(fp))
	assert read_byte(fp) == 0x78
	return data


T = TypeVar("T")


def read_list(
	fp: IO[bytes],
	fun: Callable[[IO[bytes]], T],
) -> list[T]:
	size = read_int(fp)
	toc = struct.unpack(f">{size + 1}q", fp.read(8 * (size + 1)))
	entries: list[T] = []
	for offset in toc[:-1]:
		fp.seek(offset)
		entries.append(fun(fp))
	fp.seek(toc[-1])
	return entries


def read_entry_int(fp: IO[bytes]) -> int:
	return read_int(fp)


def read_entry_source(fp: IO[bytes]) -> tuple[str, int]:
	name = read_string(fp)
	count = read_int(fp)
	return name, count


def read_entry_pairs(fp: IO[bytes]) -> tuple[int, list[tuple[str, str]]]:
	src_idx = read_short(fp)
	count = read_int(fp)
	pairs = [(read_string(fp), read_string(fp)) for i in range(count)]
	return src_idx, pairs


def read_entry_text(fp: IO[bytes]) -> tuple[int, str]:
	src_idx = read_short(fp)
	txt = read_string(fp)
	return src_idx, txt


def read_entry_html(fp: IO[bytes]) -> tuple[int, str, str]:
	src_idx = read_short(fp)
	title = read_string(fp)
	read_int(fp)  # len_raw
	len_compr = read_int(fp)
	b_compr = fp.read(len_compr)
	with gzip.open(io.BytesIO(b_compr), "r") as zf:
		# this is not modified UTF-8 (read_string), but actual UTF-8
		html = zf.read().decode()
	return src_idx, title, html


def read_entry_index(fp: IO[bytes]) -> EntryIndexTuple:
	short_name = read_string(fp)
	long_name = read_string(fp)
	iso = read_string(fp)
	normalizer_rules = read_string(fp)
	swap_flag = read_bool(fp)
	main_token_count = read_int(fp)
	index_entries = read_list(fp, read_entry_indexentry)

	stop_list_size = read_int(fp)
	stop_list_offset = fp.tell()
	stop_list = read_hashset(fp)
	assert fp.tell() == stop_list_offset + stop_list_size

	num_rows = read_int(fp)
	row_size = read_int(fp)
	row_data = fp.read(num_rows * row_size)
	rows = [
		# <type>, <index>
		struct.unpack(">bi", row_data[j : j + row_size])
		for j in range(0, len(row_data), row_size)
	]
	return (
		short_name,
		long_name,
		iso,
		normalizer_rules,
		swap_flag,
		main_token_count,
		index_entries,
		stop_list,
		rows,
	)


def read_entry_indexentry(fp: IO[bytes]) -> IndexEntryType:
	token = read_string(fp)
	start_index = read_int(fp)
	count = read_int(fp)
	has_normalized = read_bool(fp)
	token_norm = read_string(fp) if has_normalized else ""
	html_indices = read_list(fp, read_entry_int)
	return token, start_index, count, token_norm, html_indices
