from typing import TYPE_CHECKING

from pyglossary.sort_modules import ebook

if TYPE_CHECKING:
	from .sort_keys_types import sortKeyType, sqliteSortKeyType


desc = "E-Book (prefix length: 3)"


def normal(sortEncoding: str = "utf-8", **options) -> "sortKeyType":
	return ebook.normal(
		sortEncoding=sortEncoding,
		group_by_prefix_length=3,
	)


def sqlite(
	sortEncoding: str = "utf-8",
	**options,
) -> "sqliteSortKeyType":
	return ebook.sqlite(
		sortEncoding=sortEncoding,
		group_by_prefix_length=3,
	)
