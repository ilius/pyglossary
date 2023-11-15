from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from .sort_keys_types import sortKeyType, sqliteSortKeyType


desc = "ASCII-Lowercase Headword"


def normal(
	sortEncoding: str = "utf-8",
	**options,
) -> "sortKeyType":
	def sortKey(words: "list[str]") -> bytes:
		return words[0].encode(sortEncoding, errors="replace").lower()

	return sortKey


# def locale(
# 	collator: "T_Collator",  # noqa: F821
# ) -> "sortKeyType":
# 	raise NotImplementedError("")


def sqlite(sortEncoding: str = "utf-8", **options) \
	-> "sqliteSortKeyType":
	def sortKey(words: "list[str]") -> bytes:
		return words[0].encode(sortEncoding, errors="replace").lower()

	return [
		(
			"headword_blower",
			"TEXT" if sortEncoding == "utf-8" else "BLOB",
			sortKey,
		),
	]
