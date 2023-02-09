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

from os.path import (
	splitext,
)
import logging

from .compression import (
	stdCompressions,
)
from .entry import Entry
from .glossary_type import EntryType
from .sort_keys import NamedSortKey, sortKeyType

from typing import Optional, Any, List, Tuple, Dict, Iterator

log = logging.getLogger("pyglossary")


class EntryList(object):
	def __init__(self, glos):
		self._l = []
		self._glos = glos
		self._sortKey = None

	def append(self, entry: "EntryType"):
		self._l.append(entry.getRaw(self._glos))

	def insert(self, pos, entry: "EntryType"):
		self._l.insert(pos, entry.getRaw(self._glos))

	def clear(self):
		self._l.clear()

	def __len__(self):
		return len(self._l)

	def __iter__(self) -> "Iterator[EntryType]":
		glos = self._glos
		for rawEntry in self._l:
			yield Entry.fromRaw(
				glos, rawEntry,
				defaultDefiFormat=glos._defaultDefiFormat,
			)

	def _getLocaleSortKey(
		self,
		namedSortKey: "NamedSortKey",
		sortLocale: str,
		writeOptions: "Dict[str, Any]",
	) -> "sortKeyType":
		from icu import Locale, Collator

		if namedSortKey.locale is None:
			raise ValueError(
				f"locale-sorting is not supported "
				f"for sortKey={namedSortKey.name}"
			)

		localeObj = Locale(sortLocale)
		if not localeObj.getISO3Language():
			raise ValueError(f"invalid locale {sortLocale!r}")

		log.info(f"Sorting based on locale {localeObj.getName()}")

		collator = Collator.createInstance(localeObj)

		return namedSortKey.locale(collator, **writeOptions)

	def _applySortScript(
		self,
		sortKey: "sortKeyType",
		sortScript: "List[str]",
	) -> "sortKeyType":
		from pyglossary.langs.writing_system import (
			writingSystemByLowercaseName,
			getWritingSystemFromText,
		)

		wsNames = []
		for wsNameInput in sortScript:
			ws = writingSystemByLowercaseName.get(wsNameInput.lower())
			if ws is None:
				log.error(f"invalid script name {wsNameInput!r}")
				continue
			wsNames.append(ws.name)

		log.info(f"Sorting based on scripts: {wsNames}")

		def newSortKey(words: "List[str]"):
			ws = getWritingSystemFromText(words[0], True)
			if ws is None:
				return (-1, sortKey(words))  # FIXME
			try:
				index = wsNames.index(ws.name)
			except ValueError:
				index = len(wsNames)
			return (index, sortKey(words))

		return newSortKey

	def setSortKey(
		self,
		namedSortKey: "NamedSortKey",
		sortEncoding: "Optional[str]",
		sortLocale: "Optional[str]",
		sortScript: "Optional[List[str]]",
		writeOptions: "Dict[str, Any]",
	):
		if sortLocale:
			sortKey = self._getLocaleSortKey(namedSortKey, sortLocale, writeOptions)
		else:
			sortKey = namedSortKey.normal(sortEncoding, **writeOptions)
		if sortScript:
			sortKey = self._applySortScript(sortKey, sortScript)
		self._sortKey = Entry.getRawEntrySortKey(self._glos, sortKey)

	def sort(self):
		if self._sortKey is None:
			raise ValueError("EntryList.sort: sortKey is not set")
		self._l.sort(key=self._sortKey)

	def close(self):
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
