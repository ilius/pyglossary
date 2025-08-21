from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from pyglossary.sort_keys_types import SortKeyType, SQLiteSortKeyType


__all__ = ["normal", "sqlite"]

desc = "E-Book (prefix length: 2)"


def normal(
	sortEncoding: str = "utf-8",  # noqa: ARG001
	**options,
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


def sqlite(sortEncoding: str = "utf-8", **options) -> SQLiteSortKeyType:
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

	type_ = "TEXT" if sortEncoding == "utf-8" else "BLOB"
	return [
		(
			"prefix",
			type_,
			getPrefix,
		),
		(
			"headword",
			type_,
			headword,
		),
	]
