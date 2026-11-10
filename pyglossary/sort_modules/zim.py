"""
Sort glossary entries in the order libzim stores them in a Zim archive.

libzim keeps entries in sorted path order (``src/writer/creatordata.h``,
``src/writer/_dirent.h`` and ``src/writer/tinyString.h``) and verifies that
order when reading (``src/fileimpl.cpp``):
https://github.com/openzim/libzim/blob/main/src/writer/creatordata.h
https://github.com/openzim/libzim/blob/main/src/writer/_dirent.h
https://github.com/openzim/libzim/blob/main/src/writer/tinyString.h
https://github.com/openzim/libzim/blob/main/src/fileimpl.cpp

PyGlossary stores article entries under the common ``A/`` prefix (see
``pyglossary/plugins/zim/writer.py``). Since every such entry shares that prefix,
comparing the percent-encoded headwords gives the same order as comparing the
full paths. This key reproduces that order so it can be compared against the Zim
reader output.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import quote

if TYPE_CHECKING:
	from pyglossary.stubs.sort_keys_types import SortKeyType, SQLiteSortKeyType


desc = "Zim (libzim path order)"


def _zimSortKey(headword: str, sortEncoding: str) -> bytes:
	"""
	Return the part of a Zim article path that determines sort order.

	The ``A/`` prefix shared by all article entries is intentionally omitted:
	it does not change their relative order, and libzim compares the remaining
	path bytes directly. The result is encoded with ``sortEncoding`` so it can be
	compared bytewise.
	"""
	return quote(headword, safe="").encode(sortEncoding, errors="replace")


def normal(sortEncoding: str = "utf-8", **_options: Any) -> SortKeyType:
	"""Build an in-memory sort key that matches libzim path order."""

	def sortKey(words: list[str]) -> Any:
		"""Return the first headword as bytes in libzim path order."""
		return _zimSortKey(words[0], sortEncoding)

	return sortKey


def sqlite(sortEncoding: str = "utf-8", **_options: Any) -> SQLiteSortKeyType:
	"""Build a SQLite sort-key column that matches libzim path order."""

	def sortKey(words: list[str]) -> Any:
		"""Return the first headword as bytes in libzim path order."""
		return _zimSortKey(words[0], sortEncoding)

	# A single BLOB column is enough because path order is a bytewise comparison.
	return [
		(
			"zim_path",
			"BLOB",
			sortKey,
		),
	]
