from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from pyglossary.icu_types import T_Collator

	from .sort_keys_types import SortKeyType, SQLiteSortKeyType


desc = "Lowercase Headword"


def normal(sortEncoding: str = "utf-8", **_options) -> SortKeyType:
	def sortKey(words: list[str]) -> bytes:
		return words[0].lower().encode(sortEncoding, errors="replace")

	return sortKey


def locale(
	collator: "T_Collator",  # noqa: F821
) -> SortKeyType:
	cSortKey = collator.getSortKey

	def sortKey(words: list[str]) -> bytes:
		return cSortKey(words[0].lower())

	return lambda **_options: sortKey


def sqlite(
	sortEncoding: str = "utf-8",
	**_options,
) -> SQLiteSortKeyType:
	def sortKey(words: list[str]) -> bytes:
		return words[0].lower().encode(sortEncoding, errors="replace")

	return [
		(
			"headword_lower",
			"TEXT" if sortEncoding == "utf-8" else "BLOB",
			sortKey,
		),
	]


def sqlite_locale(
	collator: "T_Collator",  # noqa: F821
) -> "Callable[..., SQLiteSortKeyType]":
	cSortKey = collator.getSortKey

	def sortKey(words: list[str]) -> bytes:
		return cSortKey(words[0].lower())

	return lambda **_options: [("sortkey", "BLOB", sortKey)]
