"""
Sort glossary entries by primary headword bytes.

Uses the first alternate term encoded with the configured sort encoding; the
default lexical ordering for most conversions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from pyglossary.stubs.icu_types import T_Collator
	from pyglossary.stubs.sort_keys_types import (
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

	def wrapper(
		sortEncoding: str = "utf-8",  # noqa: ARG001
		**_options: Any,
	) -> SortKeyType:
		return sortKey

	return wrapper


def sqlite(sortEncoding: str = "utf-8", **_options: Any) -> SQLiteSortKeyType:
	def sortKey(words: list[str]) -> Any:
		return words[0].encode(sortEncoding, errors="replace")

	return [
		(
			"headword",
			"BLOB",
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
