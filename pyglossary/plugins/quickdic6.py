# -*- coding: utf-8 -*-

import datetime as dt
import functools
import gzip
import io
import math
import pathlib
import struct
import typing
import zipfile
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from typing import Literal

from pyglossary.core import log
from pyglossary.flags import NEVER
from pyglossary.glossary_types import EntryType, GlossaryType
from pyglossary.langs import langDict
from pyglossary.option import (
	Option,
	StrOption,
)
from pyglossary.plugin_lib import mutf8

enable = True
lname = "quickdic6"
format = "QuickDic6"
description = "QuickDic version 6 (.quickdic)"
extensions = (".quickdic", ".quickdic.v006.zip")
extensionCreate = ".quickdic"

sortOnWrite = NEVER

kind = "binary"
wiki = ""
website = (
	"https://github.com/rdoeffinger/Dictionary",
	"github.com/rdoeffinger/Dictionary",
)
# https://github.com/rdoeffinger/Dictionary/blob/master/dictionary-format-v6.txt
optionsProp: "dict[str, Option]" = {
	"normalizer_rules": StrOption(
		comment="ICU normalizer rules to use for index sorting",
	),
	"source_lang": StrOption(
		comment="The language of the tokens in the dictionary index",
	),
	"target_lang": StrOption(
		comment="The language of the dictionary entries",
	),
}

HASH_SET_INIT = (
	b"\xac\xed"  # magic
	b"\x00\x05"  # version
	b"\x73"  # object
	b"\x72"  # class
	# Java String "java.util.HashSet":
	b"\x00\x11\x6a\x61\x76\x61\x2e\x75\x74\x69"
	b"\x6c\x2e\x48\x61\x73\x68\x53\x65\x74"
)
"""First part of Java serialization of java.util.HashSet"""

HASH_SET_INIT2 = (
	# serialization ID:
	b"\xba\x44\x85\x95\x96\xb8\xb7\x34"
	b"\x03"  # flags: serialized, custom serialization function
	b"\x00\x00"  # fields count
	b"\x78"  # blockdata end
	b"\x70"  # null (superclass)
	b"\x77\x0c"  # blockdata short, 0xc bytes
)
"""Second part of Java serialization of java.util.HashSet"""

LINKED_HASH_SET_INIT = (
	b"\xac\xed"  # magic
	b"\x00\x05"  # version
	b"\x73"  # object
	b"\x72"  # class
	# Java String "java.util.LinkedHashSet":
	b"\x00\x17\x6a\x61\x76\x61\x2e\x75\x74\x69"
	b"\x6c\x2e\x4c\x69\x6e\x6b\x65\x64"
	b"\x48\x61\x73\x68\x53\x65\x74"
	# serialization ID:
	b"\xd8\x6c\xd7\x5a\x95\xdd\x2a\x1e"
	b"\x02"  # flags
	b"\x00\x00"  # fields count
	b"\x78"  # blockdata end
	b"\x72"  # superclass (java.util.HashSet)
	b"\x00\x11\x6a\x61\x76\x61\x2e\x75\x74\x69"
	b"\x6c\x2e\x48\x61\x73\x68\x53\x65\x74"
) + HASH_SET_INIT2
"""Header of Java serialization of java.util.LinkedHashSet"""

HASH_SET_CAPACITY_FACTOR = 0.75
"""Capacity factor used to determine the hash set's capacity from its length"""


def read_byte(fp):
	return struct.unpack(">b", fp.read(1))[0]


def write_byte(fp, val):
	return fp.write(struct.pack(">b", val))


def read_bool(fp):
	return bool(read_byte(fp))


def write_bool(fp, val):
	return write_byte(fp, val)


def read_short(fp):
	return struct.unpack(">h", fp.read(2))[0]


def write_short(fp, val):
	return fp.write(struct.pack(">h", val))


def read_int(fp):
	return struct.unpack(">i", fp.read(4))[0]


def write_int(fp, val):
	return fp.write(struct.pack(">i", val))


def read_long(fp):
	return struct.unpack(">q", fp.read(8))[0]


def write_long(fp, val):
	return fp.write(struct.pack(">q", val))


def read_float(fp):
	return struct.unpack(">f", fp.read(4))[0]


def write_float(fp, val):
	return fp.write(struct.pack(">f", val))


def read_string(fp):
	length = read_short(fp)
	return mutf8.decode_modified_utf8(fp.read(length))


def write_string(fp, val):
	b_string = mutf8.encode_modified_utf8(val)
	return write_short(fp, len(b_string)) + fp.write(b_string)


def read_hashset(fp):
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
	data = []
	while len(data) < num_entries:
		assert read_byte(fp) == 0x74
		data.append(read_string(fp))
	assert read_byte(fp) == 0x78
	return data


def write_hashset(fp, data, linked_hash_set=False):
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


def read_list(fp, fun):
	size = read_int(fp)
	toc = struct.unpack(f">{size + 1}q", fp.read(8 * (size + 1)))
	entries = []
	for offset in toc[:-1]:
		fp.seek(offset)
		entries.append(fun(fp))
	fp.seek(toc[-1])
	return entries


def write_list(fp, fun, entries):
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


def read_entry_int(fp):
	return read_int(fp)


def write_entry_int(fp, entry):
	return write_int(fp, entry)


def read_entry_source(fp):
	name = read_string(fp)
	count = read_int(fp)
	return name, count


def write_entry_source(fp, entry):
	name, count = entry
	return write_string(fp, name) + write_int(fp, count)


def read_entry_pairs(fp):
	src_idx = read_short(fp)
	count = read_int(fp)
	pairs = [(read_string(fp), read_string(fp)) for i in range(count)]
	return src_idx, pairs


def write_entry_pairs(fp, entry):
	write_start_offset = fp.tell()
	src_idx, pairs = entry
	write_short(fp, src_idx)
	write_int(fp, len(pairs))
	for p in pairs:
		write_string(fp, p[0])
		write_string(fp, p[1])
	return fp.tell() - write_start_offset


def read_entry_text(fp):
	src_idx = read_short(fp)
	txt = read_string(fp)
	return src_idx, txt


def write_entry_text(fp, entry):
	src_idx, txt = entry
	return write_short(fp, src_idx) + write_string(fp, txt)


def read_entry_html(fp):
	src_idx = read_short(fp)
	title = read_string(fp)
	read_int(fp)  # len_raw
	len_compr = read_int(fp)
	b_compr = fp.read(len_compr)
	with gzip.open(io.BytesIO(b_compr), "r") as zf:
		# this is not modified UTF-8 (read_string), but actual UTF-8
		html = zf.read().decode()
	return src_idx, title, html


def write_entry_html(fp, entry):
	write_start_offset = fp.tell()
	src_idx, title, html = entry
	b_html = "".join(
		c if ord(c) < 128 else f"&#{ord(c)};" for c in html
	).encode()
	b_compr = io.BytesIO()
	with gzip.GzipFile(fileobj=b_compr, mode="wb") as zf:
		# note that the compressed bytes might differ from the original Java
		# implementation that uses GZIPOutputStream
		zf.write(b_html)
	b_compr.seek(0)
	b_compr = b_compr.read()
	write_short(fp, src_idx)
	write_string(fp, title)
	write_int(fp, len(b_html))
	write_int(fp, len(b_compr))
	fp.write(b_compr)
	return fp.tell() - write_start_offset


def read_entry_index(fp):
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
		struct.unpack(">bi", row_data[j:j + row_size])
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


def write_entry_index(fp, entry):
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


def read_entry_indexentry(fp):
	token = read_string(fp)
	start_index = read_int(fp)
	count = read_int(fp)
	has_normalized = read_bool(fp)
	token_norm = read_string(fp) if has_normalized else ""
	html_indices = read_list(fp, read_entry_int)
	return token, start_index, count, token_norm, html_indices


def write_entry_indexentry(fp, entry):
	token, start_index, count, token_norm, html_indices = entry
	has_normalized = token_norm != ""
	write_string(fp, token)
	write_int(fp, start_index)
	write_int(fp, count)
	write_bool(fp, has_normalized)
	if has_normalized:
		write_string(fp, token_norm)
	write_list(fp, write_entry_int, html_indices)


class Comparator:
	def __init__(self, locale_str: str, normalizer_rules: str, version: int):
		import icu
		self.version = version
		self.locale = icu.Locale(locale_str)
		self._comparator = (
			icu.RuleBasedCollator("&z<ȝ")
			if self.locale.getLanguage() == "en"
			else icu.Collator.createInstance(self.locale)
		)
		self._comparator.setStrength(icu.Collator.IDENTICAL)
		self.normalizer_rules = normalizer_rules
		self.normalize = icu.Transliterator.createFromRules(
			"",
			self.normalizer_rules,
			icu.UTransDirection.FORWARD,
		).transliterate

	def compare(
		self,
		tup1: "tuple[str, str]",
		tup2: "tuple[str, str]",
	) -> "Literal[0] | Literal[1] | Literal[-1]":
		# assert isinstance(tup1, tuple)
		# assert isinstance(tup2, tuple)
		s1, n1 = tup1
		s2, n2 = tup2
		cn = self._compare_without_dash(n1, n2)
		if cn != 0:
			return cn
		cn = self._comparator.compare(n1, n2)
		if cn != 0 or self.version < 7:
			return cn
		return self._comparator.compare(s1, s2)

	def _compare_without_dash(self, a, b) -> "Literal[0] | Literal[1] | Literal[-1]":
		if self.version < 7:
			return 0
		s1 = self._without_dash(a)
		s2 = self._without_dash(b)
		return self._comparator.compare(s1, s2)

	def _without_dash(self, a: str) -> str:
		return a.replace("-", "").replace("þ", "th").replace("Þ", "Th")


class QuickDic:
	def __init__(
		self,
		name,
		sources,
		pairs,
		texts,
		htmls,
		version=6,
		indices=None,
		created=None,
	):
		self.name = name
		self.sources = sources
		self.pairs = pairs
		self.texts = texts
		self.htmls = htmls
		self.version = version
		self.indices = [] if indices is None else indices
		self.created = dt.datetime.now() if created is None else created

	@classmethod
	def from_path(cls, path):
		path = pathlib.Path(path)
		if path.suffix != ".zip":
			with open(path, "rb") as fp:
				return cls.from_fp(fp)
		with zipfile.ZipFile(path, mode="r") as zf:
			fname = [n for n in zf.namelist() if n.endswith(".quickdic")][0]
			with zf.open(fname) as fp:
				return cls.from_fp(fp)

	@classmethod
	def from_fp(cls, fp):
		version = read_int(fp)
		created = dt.datetime.fromtimestamp(float(read_long(fp)) / 1000.0)
		name = read_string(fp)
		sources = read_list(fp, read_entry_source)
		pairs = read_list(fp, read_entry_pairs)
		texts = read_list(fp, read_entry_text)
		htmls = read_list(fp, read_entry_html)
		indices = read_list(fp, read_entry_index)
		assert read_string(fp) == "END OF DICTIONARY"
		return cls(
			name,
			sources,
			pairs,
			texts,
			htmls,
			version=version,
			indices=indices,
			created=created,
		)

	def add_index(
		self,
		short_name,
		long_name,
		iso,
		normalizer_rules,
		swap_flag,
		synonyms=None,
	):
		comparator = Comparator(iso, normalizer_rules, self.version)

		synonyms = {} if synonyms is None else synonyms
		n_synonyms = sum(len(v) for v in synonyms.values())
		log.info(f"Adding an index for {iso} with {n_synonyms} synonyms ...")

		# since we don't tokenize, the stop list is always empty
		stop_list = []
		if self.indices is None:
			self.indices = []

		log.info("Initialize token list ...")
		tokens = [
			(pair[1 if swap_flag else 0], 0, idx)
			for idx, (_, pairs) in enumerate(self.pairs)
			for pair in pairs
		]
		if not swap_flag:
			tokens.extend(
				[
					(title, 4, idx)
					for idx, (_, title, _) in enumerate(self.htmls)
				],
			)
		tokens = [(t.strip(), ttype, tidx) for t, ttype, tidx in tokens]

		log.info("Normalize tokens ...")
		tokens = [
			(t, comparator.normalize(t), ttype, tidx)
			for t, ttype, tidx in tokens
			if t != ""
		]

		if len(synonyms) > 0:
			log.info(
				f"Insert synonyms into token list ({len(tokens)} entries) ...",
			)
			tokens.extend(
				[
					(s, comparator.normalize(s)) + t[2:]
					for t in tokens
					if t[0] in synonyms
					for s in synonyms[t[0]]
					if s != ""
				],
			)

		log.info(f"Sort tokens with synonyms ({len(tokens)} entries) ...")
		key_fun = functools.cmp_to_key(comparator.compare)
		tokens.sort(key=lambda t: key_fun((t[0], t[1])))

		log.info("Build mid-layer index ...")
		rows = []
		index_entries = []
		for token, token_norm, ttype, tidx in tokens:
			prev_token = (
				"" if len(index_entries) == 0 else index_entries[-1][0]
			)
			if prev_token == token:
				(
					token,
					index_start,
					count,
					token_norm,
					html_indices,
				) = index_entries.pop()
			else:
				i_entry = len(index_entries)
				index_start = len(rows)
				count = 0
				token_norm = "" if token == token_norm else token_norm
				html_indices = []
				rows.append((1, i_entry))
			if ttype == 4:
				if tidx not in html_indices:
					html_indices.append(tidx)
			else:
				if (ttype, tidx) not in rows[index_start + 1:]:
					rows.append((ttype, tidx))
					count += 1
			index_entries.append(
				(token, index_start, count, token_norm, html_indices),
			)

		# the exact meaning of this parameter is unknown,
		# and it seems to be ignored by readers
		main_token_count = len(index_entries)

		self.indices.append(
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
			),
		)

	def write(self, path):
		with open(path, "wb") as fp:
			log.info(f"Writing to {path} ...")
			write_int(fp, self.version)
			write_long(fp, int(self.created.timestamp() * 1000))
			write_string(fp, self.name)
			write_list(fp, write_entry_source, self.sources)
			write_list(fp, write_entry_pairs, self.pairs)
			write_list(fp, write_entry_text, self.texts)
			write_list(fp, write_entry_html, self.htmls)
			write_list(fp, write_entry_index, self.indices)
			write_string(fp, "END OF DICTIONARY")


class Reader:
	depends = {
		"icu": "PyICU",
	}

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._dic = None

	def open(self, filename: str) -> None:
		self._filename = filename
		self._dic = QuickDic.from_path(self._filename)
		self._glos.setDefaultDefiFormat("h")
		self._extract_synonyms_from_indices()

	def _extract_synonyms_from_indices(self):
		self._text_tokens = {}
		self._synonyms = {}
		for index in self._dic.indices:
			_, _, _, _, swap_flag, _, index_entries, _, rows = index

			# Note that we ignore swapped indices because pyglossary assumes
			# uni-directional dictionaries.
			# It might make sense to add an option in the future to read only the
			# swapped indices (create a dictionary with reversed direction).
			if swap_flag:
				continue

			for i_entry, index_entry in enumerate(index_entries):
				e_rows = self._extract_rows_from_indexentry(index, i_entry)
				token, _, _, token_norm, _ = index_entry
				for entry_id in e_rows:
					if entry_id not in self._synonyms:
						self._synonyms[entry_id] = set()
					self._synonyms[entry_id].add(token)
					if token_norm != "":
						self._synonyms[entry_id].add(token_norm)

	def _extract_rows_from_indexentry(self, index, i_entry, recurse=None):
		recurse = [] if recurse is None else recurse
		recurse.append(i_entry)
		_, _, _, _, _, _, index_entries, _, rows = index
		token, start_index, count, _, html_indices = index_entries[i_entry]
		block_rows = rows[start_index:start_index + count + 1]
		assert block_rows[0][0] in (1, 3) and block_rows[0][1] == i_entry
		e_rows = []
		for entry_type, entry_idx in block_rows[1:]:
			if entry_type in (1, 3):
				# avoid an endless recursion
				if entry_idx not in recurse:
					e_rows.extend(
						self._extract_rows_from_indexentry(
							index,
							entry_idx,
							recurse=recurse,
						),
					)
			else:
				e_rows.append((entry_type, entry_idx))
				if entry_type == 2 and entry_idx not in self._text_tokens:
					self._text_tokens[entry_idx] = token
		for idx in html_indices:
			if (4, idx) not in e_rows:
				e_rows.append((4, idx))
		return e_rows

	def close(self) -> None:
		self.clear()

	def clear(self) -> None:
		self._filename = ""
		self._dic = None

	def __len__(self) -> int:
		if self._dic is None:
			return 0
		return sum(len(p) for _, p in self._dic.pairs) + len(self._dic.htmls)

	def __iter__(self) -> "typing.Iterator[EntryType]":
		if self._dic is None:
			raise RuntimeError("dictionary not open")
		for idx, (_, pairs) in enumerate(self._dic.pairs):
			syns = self._synonyms.get((0, idx), set())
			for word, defi in pairs:
				l_word = [word] + sorted(syns.difference({word}))
				yield self._glos.newEntry(l_word, defi, defiFormat="m")
		for idx, (_, defi) in enumerate(self._dic.texts):
			if idx not in self._text_tokens:
				# Ignore this text entry since it is not mentioned in the index at all
				# so that we don't even have a token or title for it.
				continue
			word = self._text_tokens[idx]
			syns = self._synonyms.get((2, idx), set())
			l_word = [word] + sorted(syns.difference({word}))
			yield self._glos.newEntry(l_word, defi, defiFormat="m")
		for idx, (_, word, defi) in enumerate(self._dic.htmls):
			syns = self._synonyms.get((4, idx), set())
			l_word = [word] + sorted(syns.difference({word}))
			yield self._glos.newEntry(l_word, defi, defiFormat="h")


class Writer:
	_normalizer_rules = ""
	_source_lang = ""
	_target_lang = ""

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._dic = None

	def finish(self) -> None:
		self._filename = ""
		self._dic = None

	def open(self, filename: str) -> None:
		self._filename = filename

	def write(self) -> "typing.Generator[None, EntryType, None]":
		synonyms: dict[str, list[str]] = {}
		htmls = []
		log.info("Converting individual entries ...")
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				log.warn(f"Ignoring binary data entry {entry.l_word[0]}")
				continue

			entry.detectDefiFormat()
			if entry.defiFormat not in ("h", "m"):
				log.error(f"Unsupported defiFormat={entry.defiFormat}, assuming 'h'")

			words = entry.l_word
			if words[0] in synonyms:
				synonyms[words[0]].extend(words[1:])
			else:
				synonyms[words[0]] = words[1:]

			# Note that we currently write out all entries as "html" type entries.
			# In the future, it might make sense to add an option that somehow
			# specifies the entry type to use.
			htmls.append((0, words[0], entry.defi))

		log.info("Collecting meta data ...")
		name = self._glos.getInfo("bookname")
		if name == "":
			name = self._glos.getInfo("description")

		sourceLang = (
			self._glos.sourceLang
			if self._source_lang == ""
			else langDict[self._source_lang]
		)
		targetLang = (
			self._glos.targetLang
			if self._target_lang == ""
			else langDict[self._target_lang]
		)
		if sourceLang and targetLang:
			sourceLang = sourceLang.code
			targetLang = targetLang.code
		else:
			# fallback if no languages are specified
			sourceLang = targetLang = "EN"
		langs = f"{sourceLang}->{targetLang}"
		if langs not in name.lower():
			name = f"{self._glos.getInfo('name')} ({langs})"

		sources = [("", len(htmls))]
		pairs = []
		texts = []
		self._dic = QuickDic(name, sources, pairs, texts, htmls)

		short_name = long_name = iso = sourceLang
		normalizer_rules = (
			self._normalizer_rules
			if self._normalizer_rules != ""
			else ":: Lower; 'ae' > 'ä'; 'oe' > 'ö'; 'ue' > 'ü'; 'ß' > 'ss'; "
			if iso == "DE"
			else ":: Any-Latin; ' ' > ; :: Lower; :: NFD;"
			" :: [:Nonspacing Mark:] Remove; :: NFC ;"
		)
		self._dic.add_index(
			short_name,
			long_name,
			iso,
			normalizer_rules,
			False,
			synonyms=synonyms,
		)

		self._dic.write(self._filename)
