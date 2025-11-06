# -*- coding: utf-8 -*-
#
# Copyright © 2025 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from types import ModuleType
from typing import TYPE_CHECKING, Any, NamedTuple

if TYPE_CHECKING:
	from .icu_types import T_Collator, T_Locale
	from .sort_keys_types import (
		LocaleSortKeyMakerType,
		LocaleSQLiteSortKeyMakerType,
		SortKeyMakerType,
		SQLiteSortKeyMakerType,
	)

__all__ = [
	"LocaleNamedSortKey",
	"NamedSortKey",
	"defaultSortKeyName",
	"lookupSortKey",
	"namedSortKeyList",
]

defaultSortKeyName = "headword_lower"


class NamedSortKey(NamedTuple):
	name: str
	desc: str
	normal: SortKeyMakerType | None
	sqlite: SQLiteSortKeyMakerType | None


def _load_dicformids() -> ModuleType:
	from pyglossary.sort_modules import dicformids

	return dicformids


def _load_ebook_length3() -> ModuleType:
	from pyglossary.sort_modules import ebook_length3

	return ebook_length3


def _load_ebook() -> ModuleType:
	from pyglossary.sort_modules import ebook

	return ebook


def _load_headword_bytes_lower() -> ModuleType:
	from pyglossary.sort_modules import headword_bytes_lower

	return headword_bytes_lower


def _load_headword_lower() -> ModuleType:
	from pyglossary.sort_modules import headword_lower

	return headword_lower


def _load_headword() -> ModuleType:
	from pyglossary.sort_modules import headword

	return headword


def _load_random() -> ModuleType:
	from pyglossary.sort_modules import random

	return random


def _load_stardict() -> ModuleType:
	from pyglossary.sort_modules import stardict

	return stardict


@dataclass(slots=True)  # not frozen because of mod
class LocaleNamedSortKey:
	name: str
	desc: str
	load: Callable
	mod: Any = None

	@property
	def module(self) -> Any:
		if self.mod is not None:
			return self.mod
		mod = self.load()
		self.mod = mod
		return mod

	@property
	def normal(self) -> SortKeyMakerType:
		return self.module.normal

	@property
	def sqlite(self) -> SQLiteSortKeyMakerType:
		return self.module.sqlite

	@property
	def locale(self) -> LocaleSortKeyMakerType | None:
		return getattr(self.module, "locale", None)

	@property
	def sqlite_locale(self) -> LocaleSQLiteSortKeyMakerType | None:
		return getattr(self.module, "sqlite_locale", None)


namedSortKeyList = [
	LocaleNamedSortKey(
		name="headword",
		desc="Headword",
		load=_load_headword,
	),
	LocaleNamedSortKey(
		name="headword_lower",
		desc="Lowercase Headword",
		load=_load_headword_lower,
	),
	LocaleNamedSortKey(
		name="headword_bytes_lower",
		desc="ASCII-Lowercase Headword",
		load=_load_headword_bytes_lower,
	),
	LocaleNamedSortKey(
		name="stardict",
		desc="StarDict",
		load=_load_stardict,
	),
	LocaleNamedSortKey(
		name="ebook",
		desc="E-Book (prefix length: 2)",
		load=_load_ebook,
	),
	LocaleNamedSortKey(
		name="ebook_length3",
		desc="E-Book (prefix length: 3)",
		load=_load_ebook_length3,
	),
	LocaleNamedSortKey(
		name="dicformids",
		desc="DictionaryForMIDs",
		load=_load_dicformids,
	),
	LocaleNamedSortKey(
		name="random",
		desc="Random",
		load=_load_random,
	),
]

_sortKeyByName = {item.name: item for item in namedSortKeyList}


def lookupSortKey(sortKeyId: str) -> NamedSortKey | None:
	localeName: str | None = None

	parts = sortKeyId.split(":")
	if len(parts) == 1:
		(sortKeyName,) = parts
	elif len(parts) == 2:
		sortKeyName, localeName = parts
	else:
		raise ValueError(f"invalid {sortKeyId = }")

	if not sortKeyName:
		sortKeyName = defaultSortKeyName

	localeSK = _sortKeyByName.get(sortKeyName)
	if localeSK is None:
		return None

	if not localeName:
		return NamedSortKey(
			name=localeSK.name,
			desc=localeSK.desc,
			normal=localeSK.normal,
			sqlite=localeSK.sqlite,
		)

	from icu import Collator, Locale  # type: ignore

	localeObj: T_Locale = Locale(localeName)
	localeNameFull = localeObj.getName()
	collator: T_Collator = Collator.createInstance(localeObj)

	return NamedSortKey(
		name=f"{localeSK.name}:{localeNameFull}",
		desc=f"{localeSK.desc}:{localeNameFull}",
		normal=localeSK.locale(collator) if localeSK.locale else None,
		sqlite=localeSK.sqlite_locale(collator) if localeSK.sqlite_locale else None,
	)


# https://en.wikipedia.org/wiki/UTF-8#Comparison_with_other_encodings
# Sorting order: The chosen values of the leading bytes means that a list
# of UTF-8 strings can be sorted in code point order by sorting the
# corresponding byte sequences.
