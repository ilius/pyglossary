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
from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Callable, Iterator
	from typing import Any

	from .glossary_types import EntryType, RawEntryType
	from .sort_keys import NamedSortKey

from .entry import Entry

__all__ = ["EntryList"]

log = logging.getLogger("pyglossary")


class EntryList:
	def __init__(
		self,
		entryToRaw: Callable[[EntryType], RawEntryType],
		entryFromRaw: Callable[[RawEntryType], EntryType],
	) -> None:
		self._l: list[RawEntryType] = []
		self._entryToRaw = entryToRaw
		self._entryFromRaw = entryFromRaw
		self._sortKey: Callable[[RawEntryType], Any] | None = None

	def append(self, entry: EntryType) -> None:
		self._l.append(self._entryToRaw(entry))

	def clear(self) -> None:
		self._l.clear()

	def __len__(self) -> int:
		return len(self._l)

	def __iter__(self) -> Iterator[EntryType]:
		entryFromRaw = self._entryFromRaw
		for rawEntry in self._l:
			yield entryFromRaw(rawEntry)

	def hasSortKey(self) -> bool:
		return bool(self._sortKey)

	def setSortKey(
		self,
		namedSortKey: NamedSortKey,
		sortEncoding: str | None,
		writeOptions: dict[str, Any],
	) -> None:
		if namedSortKey.normal is None:
			raise NotImplementedError(
				f"sort key {namedSortKey.name!r} is not supported",
			)
		kwargs = writeOptions.copy()
		if sortEncoding:
			kwargs["sortEncoding"] = sortEncoding
		sortKey = namedSortKey.normal(**kwargs)
		self._sortKey = Entry.getRawEntrySortKey(
			key=sortKey,
		)

	def sort(self) -> None:
		if self._sortKey is None:
			raise ValueError("EntryList.sort: sortKey is not set")
		self._l.sort(key=self._sortKey)

	def close(self) -> None:
		pass
