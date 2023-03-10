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
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from typing import Any, Callable, Iterator

	from .glossary_type import EntryType, GlossaryType, RawEntryType
	from .sort_keys import NamedSortKey

from .entry import Entry

log = logging.getLogger("pyglossary")

class EntryListType(object):
	def append(self, entry: "EntryType") -> None:
		raise NotImplementedError

	def insert(self, pos: int, entry: "EntryType") -> None:
		raise NotImplementedError

	def clear(self) -> None:
		raise NotImplementedError

	def __len__(self) -> int:
		raise NotImplementedError

	def __iter__(self) -> "Iterator[EntryType]":
		raise NotImplementedError

	def setSortKey(
		self,
		namedSortKey: "NamedSortKey",
		sortEncoding: "str | None",
		writeOptions: "dict[str, Any]",
	) -> None:
		raise NotImplementedError


	def sort(self) -> None:
		raise NotImplementedError

	def close(self) -> None:
		raise NotImplementedError


class EntryList(EntryListType):
	def __init__(self, glos: "GlossaryType") -> None:
		self._l: "list[RawEntryType]" = []
		self._glos = glos
		self._sortKey: "Callable[[RawEntryType], Any] | None" = None

	def append(self, entry: "EntryType") -> None:
		self._l.append(entry.getRaw(self._glos))

	def insert(self, pos: int, entry: "EntryType") -> None:
		self._l.insert(pos, entry.getRaw(self._glos))

	def clear(self) -> None:
		self._l.clear()

	def __len__(self) -> int:
		return len(self._l)

	def __iter__(self) -> "Iterator[EntryType]":
		glos = self._glos
		defaultDefiFormat = glos.getDefaultDefiFormat()
		for rawEntry in self._l:
			yield Entry.fromRaw(
				glos, rawEntry,
				defaultDefiFormat=defaultDefiFormat,
			)

	def setSortKey(
		self,
		namedSortKey: "NamedSortKey",
		sortEncoding: "str | None",
		writeOptions: "dict[str, Any]",
	) -> None:
		kwargs = writeOptions.copy()
		if sortEncoding:
			kwargs["sortEncoding"] = sortEncoding
		sortKey = namedSortKey.normal(**kwargs)
		self._sortKey = Entry.getRawEntrySortKey(self._glos, sortKey)

	def sort(self) -> None:
		if self._sortKey is None:
			raise ValueError("EntryList.sort: sortKey is not set")
		self._l.sort(key=self._sortKey)

	def close(self) -> None:
		pass
