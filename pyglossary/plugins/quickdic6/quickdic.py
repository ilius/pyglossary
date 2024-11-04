# -*- coding: utf-8 -*-
from __future__ import annotations

import datetime as dt
import functools
import pathlib
import zipfile
from typing import IO, TYPE_CHECKING

from pyglossary.core import log

from .comparator import Comparator
from .read_funcs import (
	read_entry_html,
	read_entry_index,
	read_entry_pairs,
	read_entry_source,
	read_entry_text,
	read_int,
	read_list,
	read_long,
	read_string,
)
from .write_funcs import (
	write_entry_html,
	write_entry_index,
	write_entry_pairs,
	write_entry_source,
	write_entry_text,
	write_int,
	write_list,
	write_long,
	write_string,
)

if TYPE_CHECKING:
	from .commons import EntryIndexTuple, IndexEntryType


class QuickDic:
	def __init__(  # noqa: PLR0913
		self,
		name: str,
		sources: list[tuple[str, int]],
		pairs: list[tuple[int, list[tuple[str, str]]]],
		texts: list[tuple[int, str]],
		htmls: list[tuple[int, str, str]],
		version: int = 6,
		indices: list[EntryIndexTuple] | None = None,
		created: dt.datetime | None = None,
	) -> None:
		self.name = name
		self.sources = sources
		self.pairs = pairs
		self.texts = texts
		self.htmls = htmls
		self.version = version
		self.indices = [] if indices is None else indices
		self.created = dt.datetime.now() if created is None else created

	@classmethod
	def from_path(cls: type[QuickDic], path_str: str) -> QuickDic:
		path = pathlib.Path(path_str)
		if path.suffix != ".zip":
			with open(path, "rb") as fp:
				return cls.from_fp(fp)
		with zipfile.ZipFile(path, mode="r") as zf:
			fname = next(n for n in zf.namelist() if n.endswith(".quickdic"))
			with zf.open(fname) as fp:
				return cls.from_fp(fp)

	@classmethod
	def from_fp(cls: type[QuickDic], fp: IO[bytes]) -> QuickDic:
		version = read_int(fp)
		created = dt.datetime.fromtimestamp(float(read_long(fp)) / 1000.0)  # noqa: DTZ006
		name = read_string(fp)
		sources = read_list(fp, read_entry_source)
		pairs = read_list(fp, read_entry_pairs)
		texts = read_list(fp, read_entry_text)
		htmls = read_list(fp, read_entry_html)
		indices = read_list(fp, read_entry_index)
		assert read_string(fp) == "END OF DICTIONARY"
		return cls(
			name=name,
			sources=sources,
			pairs=pairs,
			texts=texts,
			htmls=htmls,
			version=version,
			indices=indices,
			created=created,
		)

	def add_index(  # noqa: PLR0913
		self,
		short_name: str,
		long_name: str,
		iso: str,
		normalizer_rules: str,
		synonyms: dict | None = None,
	) -> None:
		swap_flag = False
		comparator = Comparator(iso, normalizer_rules, self.version)

		synonyms = synonyms or {}
		n_synonyms = sum(len(v) for v in synonyms.values())
		log.info(f"Adding an index for {iso} with {n_synonyms} synonyms ...")

		# since we don't tokenize, the stop list is always empty
		stop_list: list[str] = []
		if self.indices is None:
			self.indices = []

		log.info("Initialize token list ...")
		tokens1 = [
			(pair[1 if swap_flag else 0], 0, idx)
			for idx, (_, pairs) in enumerate(self.pairs)
			for pair in pairs
		]
		if not swap_flag:
			tokens1.extend(
				[(title, 4, idx) for idx, (_, title, _) in enumerate(self.htmls)],
			)
		tokens1 = [(t.strip(), ttype, tidx) for t, ttype, tidx in tokens1]

		log.info("Normalize tokens ...")
		tokens = [
			(t, comparator.normalize(t), ttype, tidx) for t, ttype, tidx in tokens1 if t
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
					if s
				],
			)

		log.info(f"Sort tokens with synonyms ({len(tokens)} entries) ...")
		key_fun = functools.cmp_to_key(comparator.compare)
		tokens.sort(key=lambda t: key_fun((t[0], t[1])))

		log.info("Build mid-layer index ...")
		rows: list[tuple[int, int]] = []
		index_entries: list[IndexEntryType] = []
		for token, token_norm, ttype, tidx in tokens:
			prev_token = "" if len(index_entries) == 0 else index_entries[-1][0]
			if prev_token == token:
				(
					token,  # noqa: PLW2901
					index_start,
					count,
					token_norm,  # noqa: PLW2901
					html_indices,
				) = index_entries.pop()
			else:
				i_entry = len(index_entries)
				index_start = len(rows)
				count = 0
				token_norm = "" if token == token_norm else token_norm  # noqa: PLW2901
				html_indices = []
				rows.append((1, i_entry))
			if ttype == 4:
				if tidx not in html_indices:
					html_indices.append(tidx)
			elif (ttype, tidx) not in rows[index_start + 1 :]:
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

	def write(self, path: str) -> None:
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
