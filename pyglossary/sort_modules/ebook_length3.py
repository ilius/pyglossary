"""
Sort glossary entries for three-letter ebook index groups.

Buckets headwords by the first three characters to match ebook index pagination
used by some writers.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from pyglossary.sort_modules import ebook

if TYPE_CHECKING:
	from pyglossary.sort_keys_types import SortKeyType, SQLiteSortKeyType


desc = "E-Book (prefix length: 3)"


def normal(sortEncoding: str = "utf-8", **_options: Any) -> SortKeyType:
	return ebook.normal(
		sortEncoding=sortEncoding,
		group_by_prefix_length=3,
	)


def sqlite(
	sortEncoding: str = "utf-8",
	**_options: Any,
) -> SQLiteSortKeyType:
	return ebook.sqlite(
		sortEncoding=sortEncoding,
		group_by_prefix_length=3,
	)
