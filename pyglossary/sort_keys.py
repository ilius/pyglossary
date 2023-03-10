# -*- coding: utf-8 -*-
#
# Copyright © 2022 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
# This file is part of PyGlossary project, https://github.com/ilius/pyglossary
#
# This program is a free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program. Or on Debian systems, from /usr/share/common-licenses/GPL
# If not, see <http://www.gnu.org/licenses/gpl.txt>.

import re
from collections import namedtuple
from typing import TYPE_CHECKING, Any, Callable

if TYPE_CHECKING:
	from typing import TypeAlias

	import icu

defaultSortKeyName = "headword_lower"

NamedSortKey = namedtuple("NamedSortKey", [
	"name",
	"desc",
	"normal",
	"sqlite",
])

LocaleNamedSortKey = namedtuple("LocaleNamedSortKey", [
	"name",
	"desc",
	"normal",
	"sqlite",
	"locale",
	"sqlite_locale",
])


sortKeyType: "TypeAlias" = Callable[
	[list[str]],
	Any,
]

sqliteSortKeyType: "TypeAlias" = list[tuple[str, str, sortKeyType]]


def _headword_normal(sortEncoding: str = "utf-8", **options) -> "sortKeyType":
	def sortKey(words: "list[str]") -> bytes:
		return words[0].encode(sortEncoding, errors="replace")

	return sortKey


def _headword_locale(
	collator: "icu.Collator",  # noqa: F821
) -> "sortKeyType":
	cSortKey = collator.getSortKey

	def sortKey(words: "list[str]") -> bytes:
		return cSortKey(words[0])

	return lambda **options: sortKey


def _headword_sqlite(sortEncoding: str = "utf-8", **options) -> "sqliteSortKeyType":
	def sortKey(words: "list[str]") -> bytes:
		return words[0].encode(sortEncoding, errors="replace")

	return [
		(
			"headword",
			"TEXT" if sortEncoding == "utf-8" else "BLOB",
			sortKey,
		),
	]


def _headword_sqlite_locale(
	collator: "icu.Collator",  # noqa: F821
) -> "Callable[..., sqliteSortKeyType]":
	cSortKey = collator.getSortKey

	def sortKey(words: "list[str]") -> bytes:
		return cSortKey(words[0])

	return lambda **options: [("sortkey", "BLOB", sortKey)]


def _headword_lower_normal(sortEncoding: str = "utf-8", **options) -> "sortKeyType":
	def sortKey(words: "list[str]") -> bytes:
		return words[0].lower().encode(sortEncoding, errors="replace")

	return sortKey


def _headword_lower_locale(
	collator: "icu.Collator",  # noqa: F821
) -> "sortKeyType":
	cSortKey = collator.getSortKey

	def sortKey(words: "list[str]") -> bytes:
		return cSortKey(words[0].lower())

	return lambda **options: sortKey


def _headword_lower_sqlite(
	sortEncoding: str = "utf-8",
	**options,
) -> "sqliteSortKeyType":
	def sortKey(words: "list[str]") -> bytes:
		return words[0].lower().encode(sortEncoding, errors="replace")

	return [
		(
			"headword_lower",
			"TEXT" if sortEncoding == "utf-8" else "BLOB",
			sortKey,
		),
	]


def _headword_lower_sqlite_locale(
	collator: "icu.Collator",  # noqa: F821
) -> "Callable[..., sqliteSortKeyType]":
	cSortKey = collator.getSortKey

	def sortKey(words: "list[str]") -> bytes:
		return cSortKey(words[0].lower())

	return lambda **options: [("sortkey", "BLOB", sortKey)]


def _headword_bytes_lower_normal(
	sortEncoding: str = "utf-8",
	**options,
) -> "sortKeyType":
	def sortKey(words: "list[str]") -> bytes:
		return words[0].encode(sortEncoding, errors="replace").lower()

	return sortKey


# def _headword_bytes_lower_locale(
# 	collator: "icu.Collator",  # noqa: F821
# ) -> "sortKeyType":
# 	raise NotImplementedError("")


def _headword_bytes_lower_sqlite(sortEncoding: str = "utf-8", **options) \
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


def _stardict_normal(sortEncoding: str = "utf-8", **options) -> "sortKeyType":
	def sortKey(words: "list[str]") -> "tuple[bytes, bytes]":
		b_word = words[0].encode(sortEncoding, errors="replace")
		return (b_word.lower(), b_word)

	return sortKey


def _stardict_sqlite(sortEncoding: str = "utf-8", **options) -> "sqliteSortKeyType":
	def headword_lower(words: "list[str]") -> bytes:
		return words[0].encode(sortEncoding, errors="replace").lower()

	def headword(words: "list[str]") -> bytes:
		return words[0].encode(sortEncoding, errors="replace")

	_type = "TEXT" if sortEncoding == "utf-8" else "BLOB"
	return [
		(
			"headword_lower",
			_type,
			headword_lower,
		),
		(
			"headword",
			_type,
			headword,
		),
	]


def _ebook_normal(sortEncoding: str = "utf-8", **options) -> "sortKeyType":
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


def _ebook_sqlite(sortEncoding: str = "utf-8", **options) -> "sqliteSortKeyType":
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


def _ebook_length3_normal(sortEncoding: str = "utf-8", **options) -> "sortKeyType":
	return _ebook_normal(
		sortEncoding=sortEncoding,
		group_by_prefix_length=3,
	)


def _ebook_length3_sqlite(
	sortEncoding: str = "utf-8",
	**options,
) -> "sqliteSortKeyType":
	return _ebook_sqlite(
		sortEncoding=sortEncoding,
		group_by_prefix_length=3,
	)


def _dicformids_normal(**options) -> "sortKeyType":
	re_punc = re.compile(
		r"""[!"$§%&/()=?´`\\{}\[\]^°+*~#'\-_.:,;<>@|]*""",
	)
	re_spaces = re.compile(" +")
	re_tabs = re.compile("\t+")

	def sortKey(words: "list[str]") -> str:
		word = words[0]
		word = word.strip()
		word = re_punc.sub("", word)
		word = re_spaces.sub(" ", word)
		word = re_tabs.sub(" ", word)
		word = word.lower()
		return word  # noqa: RET504

	return sortKey


def _dicformids_sqlite(**options) -> "sqliteSortKeyType":
	return [
		(
			"headword_norm",
			"TEXT",
			_dicformids_normal(**options),
		),
	]


def _random_normal(**options) -> "sortKeyType":
	from random import random
	return lambda words: random()


def _random_locale(
	collator: "icu.Collator",  # noqa: F821
) -> "sortKeyType":
	from random import random
	return lambda **options: lambda words: random()


def _random_sqlite(**options) -> "sqliteSortKeyType":
	from random import random
	return [
		(
			"random",
			"REAL",
			lambda words: random(),
		),
	]


def _random_sqlite_locale(
	collator: "icu.Collator",  # noqa: F821
	**options,
) -> "Callable[..., sqliteSortKeyType]":
	from random import random
	return lambda **options: [
		(
			"random",
			"REAL",
			lambda words: random(),
		),
	]


namedSortKeyList = [
	LocaleNamedSortKey(
		name="headword",
		desc="Headword",
		normal=_headword_normal,
		sqlite=_headword_sqlite,
		locale=_headword_locale,
		sqlite_locale=_headword_sqlite_locale,
	),
	LocaleNamedSortKey(
		name="headword_lower",
		desc="Lowercase Headword",
		normal=_headword_lower_normal,
		sqlite=_headword_lower_sqlite,
		locale=_headword_lower_locale,
		sqlite_locale=_headword_lower_sqlite_locale,
	),
	LocaleNamedSortKey(
		name="headword_bytes_lower",
		desc="ASCII-Lowercase Headword",
		normal=_headword_bytes_lower_normal,
		sqlite=_headword_bytes_lower_sqlite,
		locale=None,
		sqlite_locale=None,
	),
	LocaleNamedSortKey(
		name="stardict",
		desc="StarDict",
		normal=_stardict_normal,
		sqlite=_stardict_sqlite,
		locale=None,
		sqlite_locale=None,
	),
	LocaleNamedSortKey(
		name="ebook",
		desc="E-Book (prefix length: 2)",
		normal=_ebook_normal,
		sqlite=_ebook_sqlite,
		locale=None,
		sqlite_locale=None,
	),
	LocaleNamedSortKey(
		name="ebook_length3",
		desc="E-Book (prefix length: 3)",
		normal=_ebook_length3_normal,
		sqlite=_ebook_length3_sqlite,
		locale=None,
		sqlite_locale=None,
	),
	LocaleNamedSortKey(
		name="dicformids",
		desc="DictionaryForMIDs",
		normal=_dicformids_normal,
		sqlite=_dicformids_sqlite,
		locale=None,
		sqlite_locale=None,
	),
	LocaleNamedSortKey(
		name="random",
		desc="Random",
		normal=_random_normal,
		sqlite=_random_sqlite,
		locale=_random_locale,
		sqlite_locale=_random_sqlite_locale,
	),
]

_sortKeyByName = {
	item.name: item for item in namedSortKeyList
}

def lookupSortKey(sortKeyId: str) -> "NamedSortKey | None":
	localeName: "str | None" = None

	parts = sortKeyId.split(":")
	if len(parts) == 1:
		sortKeyName, = parts
	elif len(parts) == 2:
		sortKeyName, localeName = parts
	else:
		raise ValueError(f"invalid {sortKeyId = }")

	if sortKeyName:
		localeSK = _sortKeyByName.get(sortKeyName)
		if localeSK is None:
			return None
	else:
		localeSK = _sortKeyByName[defaultSortKeyName]

	if not localeName:
		return NamedSortKey(
			name=localeSK.name,
			desc=localeSK.desc,
			normal=localeSK.normal,
			sqlite=localeSK.sqlite,
		)

	from icu import Collator, Locale

	localeObj = Locale(localeName)
	localeNameFull = localeObj.getName()
	collator = Collator.createInstance(localeObj)

	return NamedSortKey(
		name=f"{localeSK.name}:{localeNameFull}",
		desc=f"{localeSK.desc}:{localeNameFull}",
		normal=localeSK.locale(collator),
		sqlite=localeSK.sqlite_locale(collator),
	)




"""
https://en.wikipedia.org/wiki/UTF-8#Comparison_with_other_encodings

Sorting order: The chosen values of the leading bytes means that a list
of UTF-8 strings can be sorted in code point order by sorting the
corresponding byte sequences.
"""
