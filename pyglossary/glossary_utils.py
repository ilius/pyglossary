# -*- coding: utf-8 -*-
# glossary_utils.py
#
# Copyright © 2008-2022 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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
from os.path import (
	splitext,
)
from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from typing import Any, Dict, Iterator, Optional, Tuple

	from .glossary_type import EntryType, GlossaryType
	from .sort_keys import NamedSortKey

from .compression import (
	stdCompressions,
)
from .entry import Entry

log = logging.getLogger("pyglossary")


class EntryList(object):
	def __init__(self, glos: "GlossaryType") -> None:
		self._l = []
		self._glos = glos
		self._sortKey = None

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
		for rawEntry in self._l:
			yield Entry.fromRaw(
				glos, rawEntry,
				defaultDefiFormat=glos._defaultDefiFormat,
			)

	def setSortKey(
		self,
		namedSortKey: "NamedSortKey",
		sortEncoding: "Optional[str]",
		writeOptions: "Dict[str, Any]",
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


def splitFilenameExt(
	filename: str = "",
) -> "Tuple[str, str, str]":
	"""
	returns (filenameNoExt, ext, compression)
	"""
	compression = ""
	filenameNoExt, ext = splitext(filename)
	ext = ext.lower()

	if not ext and len(filenameNoExt) < 5:
		filenameNoExt, ext = "", filenameNoExt

	if not ext:
		return filename, filename, "", ""

	if ext[1:] in stdCompressions + ("zip", "dz"):
		compression = ext[1:]
		filename = filenameNoExt
		filenameNoExt, ext = splitext(filename)
		ext = ext.lower()

	return filenameNoExt, filename, ext, compression
