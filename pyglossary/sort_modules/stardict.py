"""
Sort glossary entries the way StarDict indexes expect.

Produces lower-then-original byte tuple keys matching StarDict's default
case-insensitive collation behavior.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from pyglossary.stubs.sort_keys_types import SortKeyType, SQLiteSortKeyType


desc = "StarDict"


def normal(sortEncoding: str = "utf-8", **_options: Any) -> SortKeyType:
	def sortKey(words: list[str]) -> Any:
		b_term = words[0].encode(sortEncoding, errors="replace")
		return (b_term.lower(), b_term)

	return sortKey


def sqlite(sortEncoding: str = "utf-8", **_options: Any) -> SQLiteSortKeyType:
	def headword_lower(words: list[str]) -> Any:
		return words[0].encode(sortEncoding, errors="replace").lower()

	def headword(words: list[str]) -> Any:
		return words[0].encode(sortEncoding, errors="replace")

	return [
		(
			"headword_lower",
			"BLOB",
			headword_lower,
		),
		(
			"headword",
			"BLOB",
			headword,
		),
	]
