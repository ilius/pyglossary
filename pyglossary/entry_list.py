# -*- coding: utf-8 -*-
# entry_list.py
#
# Copyright © 2020-2023 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

import logging
import typing
from typing import TYPE_CHECKING

from .glossary_types import EntryListType

if TYPE_CHECKING:
	from typing import Any, Callable, Iterator

	from .glossary_types import EntryType, RawEntryType
	from .sort_keys import NamedSortKey

from .entry import Entry

log = logging.getLogger("pyglossary")


# although issubclass(EntryListType, EntryList) is true without inheriting
# from EntryListType, mypy does not understand this (IDK why),
# so I have to inherit from it to make mypy happy!
class EntryList(EntryListType):
	def __init__(
		self: "typing.Self",
		entryToRaw: "Callable[[EntryType], RawEntryType]",
		entryFromRaw: "Callable[[RawEntryType], EntryType]",
	) -> None:
		self._l: "list[RawEntryType]" = []
		self._entryToRaw = entryToRaw
		self._entryFromRaw = entryFromRaw
		self._sortKey: "Callable[[RawEntryType], Any] | None" = None
		self._rawEntryCompress = False

	@property
	def rawEntryCompress(self: "typing.Self") -> bool:
		return self._rawEntryCompress

	@rawEntryCompress.setter
	def rawEntryCompress(self: "typing.Self", enable: bool) -> None:
		self._rawEntryCompress = enable

	def append(self: "typing.Self", entry: "EntryType") -> None:
		self._l.append(self._entryToRaw(entry))

	def clear(self: "typing.Self") -> None:
		self._l.clear()

	def __len__(self: "typing.Self") -> int:
		return len(self._l)

	def __iter__(self: "typing.Self") -> "Iterator[EntryType]":
		entryFromRaw = self._entryFromRaw
		for rawEntry in self._l:
			yield entryFromRaw(rawEntry)

	def setSortKey(
		self: "typing.Self",
		namedSortKey: "NamedSortKey",
		sortEncoding: "str | None",
		writeOptions: "dict[str, Any]",
	) -> None:
		kwargs = writeOptions.copy()
		if sortEncoding:
			kwargs["sortEncoding"] = sortEncoding
		sortKey = namedSortKey.normal(**kwargs)
		self._sortKey = Entry.getRawEntrySortKey(
			key=sortKey,
			rawEntryCompress=self._rawEntryCompress,
		)

	def sort(self: "typing.Self") -> None:
		if self._sortKey is None:
			raise ValueError("EntryList.sort: sortKey is not set")
		self._l.sort(key=self._sortKey)

	def close(self: "typing.Self") -> None:
		pass
