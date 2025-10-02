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


desc = "Headword"


def normal(sortEncoding: str = "utf-8", **_options: Any) -> SortKeyType:
	def sortKey(words: list[str]) -> Any:
		return words[0].encode(sortEncoding, errors="replace")

	return sortKey


def locale(
	collator: T_Collator,  # noqa: F821
) -> SortKeyMakerType:
	cSortKey = collator.getSortKey

	def sortKey(words: list[str]) -> Any:
		return cSortKey(words[0])

	def warpper(
		sortEncoding: str = "utf-8",  # noqa: ARG001
		**_options: Any,
	) -> SortKeyType:
		return sortKey

	return warpper


def sqlite(sortEncoding: str = "utf-8", **_options: Any) -> SQLiteSortKeyType:
	def sortKey(words: list[str]) -> Any:
		return words[0].encode(sortEncoding, errors="replace")

	return [
		(
			"headword",
			"TEXT" if sortEncoding == "utf-8" else "BLOB",
			sortKey,
		),
	]


def sqlite_locale(
	collator: T_Collator,  # noqa: F821
) -> SQLiteSortKeyMakerType:
	cSortKey = collator.getSortKey

	def sortKey(words: list[str]) -> Any:
		return cSortKey(words[0])

	def wrapper(
		sortEncoding: str = "",  # noqa: ARG001
		**_options: Any,
	) -> SQLiteSortKeyType:
		return [("sortkey", "BLOB", sortKey)]

	return wrapper
