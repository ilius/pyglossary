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

from .interfaces import Interface

if TYPE_CHECKING:
	from typing import Any, Callable, Iterator

	from .glossary_types import EntryType, GlossaryType, RawEntryType
	from .sort_keys import NamedSortKey

from .entry import Entry

log = logging.getLogger("pyglossary")

class EntryListType(metaclass=Interface):
	def append(self: "typing.Self", entry: "EntryType") -> None:
		raise NotImplementedError

	def clear(self: "typing.Self") -> None:
		raise NotImplementedError

	def __len__(self: "typing.Self") -> int:
		raise NotImplementedError

	def __iter__(self: "typing.Self") -> "Iterator[EntryType]":
		raise NotImplementedError

	def setSortKey(
		self: "typing.Self",
		namedSortKey: "NamedSortKey",
		sortEncoding: "str | None",
		writeOptions: "dict[str, Any]",
	) -> None:
		raise NotImplementedError


	def sort(self: "typing.Self") -> None:
		raise NotImplementedError

	def close(self: "typing.Self") -> None:
		raise NotImplementedError


class EntryList:
	def __init__(
		self: "typing.Self",
		glos: "GlossaryType",
		entryToRaw: "Callable[[EntryType], RawEntryType]",
	) -> None:
		self._l: "list[RawEntryType]" = []
		self._glos = glos
		self._entryToRaw = entryToRaw
		self._sortKey: "Callable[[RawEntryType], Any] | None" = None

	def append(self: "typing.Self", entry: "EntryType") -> None:
		self._l.append(self._entryToRaw(entry))

	def clear(self: "typing.Self") -> None:
		self._l.clear()

	def __len__(self: "typing.Self") -> int:
		return len(self._l)

	def __iter__(self: "typing.Self") -> "Iterator[EntryType]":
		glos = self._glos
		defaultDefiFormat = glos.getDefaultDefiFormat()
		for rawEntry in self._l:
			yield Entry.fromRaw(
				rawEntry,
				defaultDefiFormat=defaultDefiFormat,
			)

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
		self._sortKey = Entry.getRawEntrySortKey(self._glos, sortKey)

	def sort(self: "typing.Self") -> None:
		if self._sortKey is None:
			raise ValueError("EntryList.sort: sortKey is not set")
		self._l.sort(key=self._sortKey)

	def close(self: "typing.Self") -> None:
		pass
