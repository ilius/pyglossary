"""
Read QuickDic version 6 ``.quickdic`` archives.

Unpacks QuickDic v6 ZIP bundles and reads binary index and definition stores.
Reconstructs glossary entries with sorting and collation rules from the QuickDic
format.
"""

from __future__ import annotations

import datetime as dt
import pathlib
import zipfile
from typing import IO, TYPE_CHECKING

from pyglossary.utils.html_utils import unescape_unicode

from .quickdic import QuickDic
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

if TYPE_CHECKING:
	from collections.abc import Iterator

	from pyglossary.stubs.glossary_types import EntryType, ReaderGlossaryType

	from .commons import EntryIndexTuple

__all__ = ["Reader"]


class Reader:
	"""Read QuickDic 6 glossary files."""

	useByteProgress = False
	depends = {
		"icu": "pyicu",
	}

	def __init__(self, glos: ReaderGlossaryType) -> None:
		self._glos = glos
		self._dic: QuickDic | None = None

	def open(self, filename: str) -> None:
		self._filename = filename
		self._dic = self.quickdic_from_path(self._filename)
		self._glos.setDefaultDefiFormat("h")
		self._extract_synonyms_from_indices()
		# TODO: read glossary name and langs?

	@classmethod
	def quickdic_from_path(cls: type[Reader], path_str: str) -> QuickDic:
		path = pathlib.Path(path_str)
		if path.suffix != ".zip":
			with open(path, "rb") as fp:
				return cls.quickdic_from_fp(fp)
		with zipfile.ZipFile(path, mode="r") as zf:
			fname = next(n for n in zf.namelist() if n.endswith(".quickdic"))
			with zf.open(fname) as fp:
				return cls.quickdic_from_fp(fp)

	@staticmethod
	def quickdic_from_fp(fp: IO[bytes]) -> QuickDic:
		version = read_int(fp)
		created = dt.datetime.fromtimestamp(float(read_long(fp)) / 1000.0)  # noqa: DTZ006
		name = read_string(fp)
		sources = read_list(fp, read_entry_source)
		pairs = read_list(fp, read_entry_pairs)
		texts = read_list(fp, read_entry_text)
		htmls = read_list(fp, read_entry_html)
		indices = read_list(fp, read_entry_index)
		endStr = read_string(fp)
		assert endStr == "END OF DICTIONARY", f"{endStr=}"
		return QuickDic(
			name=name,
			sources=sources,
			pairs=pairs,
			texts=texts,
			htmls=htmls,
			version=version,
			indices=indices,
			created=created,
		)

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
	) -> list[tuple[int, int]]:
		_, _, _, _, _, _, index_entries, _, rows = index
		e_rows: list[tuple[int, int]] = []
		visited: set[int] = set()
		# (kind, entry_type, entry_idx, token); "header" and "html" use
		# only entry_idx, while "row" uses all fields. The stack is used
		# instead of recursion because some entries form very deep chains.
		stack: list[tuple[str, int, int, str]] = [("header", 0, i_entry, "")]
		while stack:
			kind, entry_type, entry_idx, token = stack.pop()
			if kind == "html":
				if (4, entry_idx) not in e_rows:
					e_rows.append((4, entry_idx))
				continue
			if kind == "row":
				e_rows.append((entry_type, entry_idx))
				if entry_type == 2 and entry_idx not in self._text_tokens:
					self._text_tokens[entry_idx] = token
				continue

			if entry_idx in visited:
				continue
			visited.add(entry_idx)
			token, start_index, count, _, html_indices = index_entries[entry_idx]
			block_rows = rows[start_index : start_index + count + 1]
			assert block_rows[0][0] in {1, 3}, f"{block_rows[0][0]=}"
			assert block_rows[0][1] == entry_idx, f"{block_rows[0][1]=}"

			stack.extend(("html", 0, idx, "") for idx in reversed(html_indices))
			for row_type, row_idx in reversed(block_rows[1:]):
				if row_type in {1, 3}:
					# avoid an endless loop
					stack.append(("header", 0, row_idx, ""))
				else:
					stack.append(("row", row_type, row_idx, token))
		return e_rows

	def close(self) -> None:
		self.clear()

	def clear(self) -> None:
		self._filename = ""
		self._dic = None

	def countResourceFiles(self) -> int:
		return 0

	def __len__(self) -> int:
		if self._dic is None:
			return 0
		return sum(len(p) for _, p in self._dic.pairs) + len(self._dic.htmls)

	def __iter__(self) -> Iterator[EntryType]:
		if self._dic is None:
			raise RuntimeError("dictionary not open")
		for idx, (_, pairs) in enumerate(self._dic.pairs):
			syns = self._synonyms.get((0, idx), set())
			for term, defi in pairs:
				l_term = [term] + sorted(syns.difference({term}))
				yield self._glos.newEntry(l_term, defi, defiFormat="m")
		for idx, (_, defi) in enumerate(self._dic.texts):
			if idx not in self._text_tokens:
				# Ignore this text entry since it is not mentioned in the index at all
				# so that we don't even have a token or title for it.
				continue
			term = self._text_tokens[idx]
			syns = self._synonyms.get((2, idx), set())
			l_term = [term] + sorted(syns.difference({term}))
			yield self._glos.newEntry(l_term, defi, defiFormat="m")
		for idx, (_, term, defi) in enumerate(self._dic.htmls):
			syns = self._synonyms.get((4, idx), set())
			l_term = [term] + sorted(syns.difference({term}))
			defi_new = unescape_unicode(defi)
			yield self._glos.newEntry(l_term, defi_new, defiFormat="h")
