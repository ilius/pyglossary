from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from .sort_keys_types import SortKeyType, SQLiteSortKeyType


desc = "StarDict"


def normal(sortEncoding: str = "utf-8", **_options) -> SortKeyType:
	def sortKey(words: list[str]) -> "tuple[bytes, bytes]":
		b_word = words[0].encode(sortEncoding, errors="replace")
		return (b_word.lower(), b_word)

	return sortKey


def sqlite(sortEncoding: str = "utf-8", **_options) -> SQLiteSortKeyType:
	def headword_lower(words: list[str]) -> bytes:
		return words[0].encode(sortEncoding, errors="replace").lower()

	def headword(words: list[str]) -> bytes:
		return words[0].encode(sortEncoding, errors="replace")

	_type = "TEXT" if sortEncoding == "utf-8" else "BLOB"
	return [
		(
			"headword_lower",
			_type,
			headword_lower,
		),
		(
			"headword",
			_type,
			headword,
		),
	]
