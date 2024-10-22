from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from .sort_keys_types import SortKeyType, SQLiteSortKeyType


__all__ = ["normal", "sqlite"]

desc = "E-Book (prefix length: 2)"


def normal(
	sortEncoding: str = "utf-8",  # noqa: ARG001
	**options,
) -> SortKeyType:
	length = options.get("group_by_prefix_length", 2)

	# FIXME: return bytes
	def sortKey(words: list[str]) -> "tuple[str, str]":
		word = words[0]
		if not word:
			return "", ""
		prefix = word[:length].lower()
		if prefix[0] < "a":
			return "SPECIAL", word
		return prefix, word

	return sortKey


def sqlite(sortEncoding: str = "utf-8", **options) -> SQLiteSortKeyType:
	length = options.get("group_by_prefix_length", 2)

	def getPrefix(words: list[str]) -> str:
		word = words[0]
		if not word:
			return ""
		prefix = word[:length].lower()
		if prefix[0] < "a":
			return "SPECIAL"
		return prefix

	def headword(words: list[str]) -> bytes:
		return words[0].encode(sortEncoding, errors="replace")

	_type = "TEXT" if sortEncoding == "utf-8" else "BLOB"
	return [
		(
			"prefix",
			_type,
			getPrefix,
		),
		(
			"headword",
			_type,
			headword,
		),
	]
