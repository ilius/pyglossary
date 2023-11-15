from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from .sort_keys_types import sortKeyType, sqliteSortKeyType


desc = "E-Book (prefix length: 2)"


def normal(sortEncoding: str = "utf-8", **options) -> "sortKeyType":
	length = options.get("group_by_prefix_length", 2)

	# FIXME: return bytes
	def sortKey(words: "list[str]") -> "tuple[str, str]":
		word = words[0]
		if not word:
			return "", ""
		prefix = word[:length].lower()
		if prefix[0] < "a":
			return "SPECIAL", word
		return prefix, word

	return sortKey


def sqlite(sortEncoding: str = "utf-8", **options) -> "sqliteSortKeyType":
	length = options.get("group_by_prefix_length", 2)

	def getPrefix(words: "list[str]") -> str:
		word = words[0]
		if not word:
			return ""
		prefix = word[:length].lower()
		if prefix[0] < "a":
			return "SPECIAL"
		return prefix

	def headword(words: "list[str]") -> bytes:
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
