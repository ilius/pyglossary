# -*- coding: utf-8 -*-
from __future__ import annotations

import typing
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from pyglossary.glossary_types import EntryType, GlossaryType

	from .commons import EntryIndexTuple

from pyglossary.html_utils import unescape_unicode

from .quickdic import QuickDic


class Reader:
	depends = {
		"icu": "PyICU",
	}

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._dic: QuickDic | None = None

	def open(self, filename: str) -> None:
		self._filename = filename
		self._dic = QuickDic.from_path(self._filename)
		self._glos.setDefaultDefiFormat("h")
		self._extract_synonyms_from_indices()
		# TODO: read glossary name and langs?

	def _extract_synonyms_from_indices(self) -> None:
		self._text_tokens: dict[int, str] = {}
		self._synonyms: dict[tuple[int, int], set[str]] = {}
		assert self._dic is not None
		for index in self._dic.indices:
			_, _, _, _, swap_flag, _, index_entries, _, _ = index

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
					if token_norm:
						self._synonyms[entry_id].add(token_norm)

	def _extract_rows_from_indexentry(
		self,
		index: EntryIndexTuple,
		i_entry: int,
		recurse: list[int] | None = None,
	) -> list[tuple[int, int]]:
		recurse = recurse or []
		recurse.append(i_entry)
		_, _, _, _, _, _, index_entries, _, rows = index
		token, start_index, count, _, html_indices = index_entries[i_entry]
		block_rows = rows[start_index : start_index + count + 1]
		assert block_rows[0][0] in {1, 3}
		assert block_rows[0][1] == i_entry
		e_rows = []
		for entry_type, entry_idx in block_rows[1:]:
			if entry_type in {1, 3}:
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

	def __iter__(self) -> typing.Iterator[EntryType]:
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
			defi_new = unescape_unicode(defi)
			yield self._glos.newEntry(l_word, defi_new, defiFormat="h")
