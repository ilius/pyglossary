"""
Sort glossary entries in the order QuickDic 6 builds its index.

QuickDic 6 normalizes each headword and compares it with an ICU collator
(see ``pyglossary/plugins/quickdic6/comparator.py``). This key reproduces that
order so it can be compared against the generated QuickDic index.

Upstream sources (rdoeffinger/Dictionary, Android app):
- Format spec, index section: https://github.com/rdoeffinger/Dictionary/blob/main/dictionary-format-v6.txt
- Comparison logic: https://github.com/rdoeffinger/Dictionary/blob/main/src/com/hughes/android/dictionary/engine/NormalizeComparator.java
- Per-entry wrapper: https://github.com/rdoeffinger/Dictionary/blob/main/src/com/hughes/android/dictionary/engine/FastNormalizeComparator.java
- Runtime lookup (binary search over the sorted index): https://github.com/rdoeffinger/Dictionary/blob/main/src/com/hughes/android/dictionary/engine/Index.java

Known difference: for version 6, the Java comparator breaks ties between
normalized-equal headwords by comparing the original strings
(``compareNormalized``). ``Comparator.sort_key_parts`` returns only the
normalized collation key for version 6, so such ties are not ordered by the
original string here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
	from pyglossary.stubs.sort_keys_types import SortKeyType, SQLiteSortKeyType


desc = "QuickDic 6"


def _makeComparator(options: dict[str, Any]) -> Any:
	"""
	Build the QuickDic ``Comparator`` from sort-key options.

	Options: ``language`` (or ``iso``, default ``en``), ``normalizer_rules``
	(ICU transliteration rules; defaults to the German or generic rules in
	``pyglossary/plugins/quickdic6/commons.py``), and ``version`` (default 6).
	The imports are local so that PyICU is only needed when a sort key is used.
	"""
	from pyglossary.plugins.quickdic6.commons import (
		defaultNormalizerRules,
		defaultNormalizerRulesDE,
	)
	from pyglossary.plugins.quickdic6.comparator import Comparator

	# Mirrors the upstream sort language and rules, see Index.java:
	# sortLanguage (ISO code) and normalizerRules are stored per index.
	language = options.get("language") or options.get("iso") or "en"
	normalizerRules = options.get("normalizer_rules") or (
		defaultNormalizerRulesDE if language.upper() == "DE" else defaultNormalizerRules
	)
	version = int(options.get("version", 6))
	return Comparator(language, normalizerRules, version)


def normal(
	sortEncoding: str = "utf-8",  # noqa: ARG001
	**_options: Any,
) -> SortKeyType:
	"""
	Return an in-memory key that orders headwords like QuickDic 6.

	The key is a tuple of ICU collation keys (one for version 6, three for
	version 7 and later). Tuple comparison matches ``Comparator.compare``.
	"""
	comparator = _makeComparator(_options)

	def sortKey(words: list[str]) -> Any:
		return comparator.sort_key_parts(words[0])

	return sortKey


def sqlite(
	sortEncoding: str = "utf-8",  # noqa: ARG001
	**_options: Any,
) -> SQLiteSortKeyType:
	"""
	Return one BLOB column per part of the QuickDic sort key.

	Column order matches the tuple from ``sort_key_parts``, so an
	``ORDER BY`` over the columns in sequence gives the same order as the
	in-memory key.
	"""
	comparator = _makeComparator(_options)

	# Version 7 adds dash-folded and original-string parts; see
	# Comparator.compare and NormalizeComparator.java (compareWithoutDash).
	if comparator.version >= 7:
		columnNames = ("without_dash", "normalized", "original")
	else:
		columnNames = ("collation_key",)

	def makeValueFunc(index: int) -> SortKeyType:
		# Each column recomputes sort_key_parts and takes one part.
		def sortKey(words: list[str]) -> Any:
			return comparator.sort_key_parts(words[0])[index]

		return sortKey

	return [
		(columnName, "BLOB", makeValueFunc(index))
		for index, columnName in enumerate(columnNames)
	]
