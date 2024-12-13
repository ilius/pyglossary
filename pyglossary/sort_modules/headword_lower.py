from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from pyglossary.icu_types import T_Collator
	from pyglossary.sort_keys_types import (
		SortKeyMakerType,
		SortKeyType,
		SQLiteSortKeyMakerType,
		SQLiteSortKeyType,
	)


desc = "Lowercase Headword"


def normal(sortEncoding: str = "utf-8", **_options) -> SortKeyType:
	def sortKey(words: list[str]) -> Any:
		# assert isinstance(words, list)  # OK
		return words[0].lower().encode(sortEncoding, errors="replace")

	return sortKey


def locale(
	collator: T_Collator,  # noqa: F821
) -> SortKeyMakerType:
	cSortKey = collator.getSortKey

	def sortKey(words: list[str]) -> Any:
		# assert isinstance(words, list)  # OK
		return cSortKey(words[0].lower())

	def warpper(sortEncoding: str = "utf-8", **_options) -> SortKeyType:  # noqa: ARG001
		return sortKey

	return warpper


def sqlite(
	sortEncoding: str = "utf-8",
	**_options,
) -> SQLiteSortKeyType:
	def sortKey(words: list[str]) -> Any:
		return words[0].lower().encode(sortEncoding, errors="replace")

	return [
		(
			"headword_lower",
			"TEXT" if sortEncoding == "utf-8" else "BLOB",
			sortKey,
		),
	]


def sqlite_locale(
	collator: T_Collator,  # noqa: F821
) -> SQLiteSortKeyMakerType:
	cSortKey = collator.getSortKey

	def sortKey(words: list[str]) -> Any:
		return cSortKey(words[0].lower())

	def wrapper(sortEncoding: str = "", **_options) -> SQLiteSortKeyType:  # noqa: ARG001
		return [("sortkey", "BLOB", sortKey)]

	return wrapper
