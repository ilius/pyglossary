"""
Sort glossary entries for ebook dictionary output.

Orders headwords the way ebook writers (EPUB, MOBI, Kobo) expect when building
chapter and index pages.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from pyglossary.stubs.sort_keys_types import SortKeyType, SQLiteSortKeyType


__all__ = ["normal", "sqlite"]

desc = "E-Book (prefix length: 2)"


def normal(
	sortEncoding: str = "utf-8",  # noqa: ARG001
	**options: Any,
) -> SortKeyType:
	length = options.get("group_by_prefix_length", 2)

	def sortKey(words: list[str]) -> Any:
		term = words[0]
		if not term:
			return "", ""
		prefix = term[:length].lower()
		if prefix[0] < "a":
			return "SPECIAL", term
		return prefix, term

	return sortKey


def sqlite(sortEncoding: str = "utf-8", **options: Any) -> SQLiteSortKeyType:
	length = options.get("group_by_prefix_length", 2)

	def getPrefix(words: list[str]) -> str:
		term = words[0]
		if not term:
			return ""
		prefix = term[:length].lower()
		if prefix[0] < "a":
			return "SPECIAL"
		return prefix

	def headword(words: list[str]) -> Any:
		return words[0].encode(sortEncoding, errors="replace")

	return [
		(
			"prefix",
			"BLOB",
			getPrefix,
		),
		(
			"headword",
			"BLOB",
			headword,
		),
	]
