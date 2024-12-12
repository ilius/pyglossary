from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from pyglossary.sort_keys_types import SortKeyType, SQLiteSortKeyType


desc = "StarDict"


def normal(sortEncoding: str = "utf-8", **_options) -> SortKeyType:
	def sortKey(words: list[str]) -> Any:
		b_word = words[0].encode(sortEncoding, errors="replace")
		return (b_word.lower(), b_word)

	return sortKey


def sqlite(sortEncoding: str = "utf-8", **_options) -> SQLiteSortKeyType:
	def headword_lower(words: list[str]) -> Any:
		return words[0].encode(sortEncoding, errors="replace").lower()

	def headword(words: list[str]) -> Any:
		return words[0].encode(sortEncoding, errors="replace")

	type_ = "TEXT" if sortEncoding == "utf-8" else "BLOB"
	return [
		(
			"headword_lower",
			type_,
			headword_lower,
		),
		(
			"headword",
			type_,
			headword,
		),
	]
