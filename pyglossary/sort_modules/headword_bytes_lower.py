from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from .sort_keys_types import SortKeyType, SQLiteSortKeyType


desc = "ASCII-Lowercase Headword"


def normal(
	sortEncoding: str = "utf-8",
	**_options,
) -> SortKeyType:
	def sortKey(words: list[str]) -> bytes:
		return words[0].encode(sortEncoding, errors="replace").lower()

	return sortKey


# def locale(
# 	collator: "T_Collator",  # noqa: F821
# ) -> SortKeyType:
# 	raise NotImplementedError("")


def sqlite(sortEncoding: str = "utf-8", **_options) -> SQLiteSortKeyType:
	def sortKey(words: list[str]) -> bytes:
		return words[0].encode(sortEncoding, errors="replace").lower()

	return [
		(
			"headword_blower",
			"TEXT" if sortEncoding == "utf-8" else "BLOB",
			sortKey,
		),
	]
