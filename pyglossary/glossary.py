# -*- coding: utf-8 -*-
# glossary.py
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

from time import time as now
from typing import TYPE_CHECKING

from .core import log
from .glossary_v2 import ConvertArgs, GlossaryCommon
from .sort_keys import lookupSortKey

if TYPE_CHECKING:
	from typing import Any

	from .glossary_types import EntryType


class Glossary(GlossaryCommon):
	GLOSSARY_API_VERSION = "1.0"

	def titleElement(  # noqa: ANN201
		self,
		hf,  # type: ignore
		sample: str = "",
	):  # type: ignore
		return hf.element(self.titleTag(sample))

	def read(
		self,
		filename: str,
		format: str = "",
		direct: bool = False,
		progressbar: bool = True,
		**kwargs,  # noqa: ANN
	) -> bool:
		"""
		Read from a given glossary file.

		Parameters
		----------
		filename (str):	name/path of input file
		format (str):	name of input format,
						or "" to detect from file extension
		direct (bool):	enable direct mode
		progressbar (bool): enable progressbar.

		read-options can be passed as additional keyword arguments
		"""
		if type(filename) is not str:
			raise TypeError("filename must be str")
		if format is not None and type(format) is not str:
			raise TypeError("format must be str")

		# don't allow direct=False when there are readers
		# (read is called before with direct=True)
		if self._readers and not direct:
			raise ValueError(
				f"there are already {len(self._readers)} readers"
				f", you can not read with direct=False mode",
			)

		self._setTmpDataDir(filename)

		self._progressbar = progressbar

		ok = self._read(
			filename=filename,
			format=format,
			direct=direct,
			**kwargs,
		)
		if not ok:
			return False

		return True

	def addEntryObj(self, entry: "EntryType") -> None:
		self._data.append(entry)

	def updateIter(self) -> None:
		log.warning("calling glos.updateIter() is no longer needed.")

	def sortWords(
		self,
		sortKeyName: "str" = "headword_lower",
		sortEncoding: "str" = "utf-8",
		writeOptions: "dict[str, Any] | None" = None,
	) -> None:
		"""sortKeyName: see doc/sort-key.md."""
		if self._readers:
			raise NotImplementedError(
				"can not use sortWords in direct mode",
			)

		if self._sqlite:
			raise NotImplementedError(
				"can not use sortWords in SQLite mode",
			)

		namedSortKey = lookupSortKey(sortKeyName)
		if namedSortKey is None:
			log.critical(f"invalid {sortKeyName = }")
			return

		if not sortEncoding:
			sortEncoding = "utf-8"
		if writeOptions is None:
			writeOptions = {}

		t0 = now()
		self._data.setSortKey(
			namedSortKey=namedSortKey,
			sortEncoding=sortEncoding,
			writeOptions=writeOptions,
		)
		self._data.sort()
		log.info(f"Sorting took {now() - t0:.1f} seconds")

		self._sort = True
		self._iter = self._loadedEntryGen()

	def convert(
		self,
		inputFilename: str,
		inputFormat: str = "",
		direct: "bool | None" = None,
		progressbar: bool = True,
		outputFilename: str = "",
		outputFormat: str = "",
		sort: "bool | None" = None,
		sortKeyName: "str | None" = None,
		sortEncoding: "str | None" = None,
		readOptions: "dict[str, Any] | None" = None,
		writeOptions: "dict[str, Any] | None" = None,
		sqlite: "bool | None" = None,
		infoOverride: "dict[str, str] | None" = None,
	) -> "str | None":
		self.progressbar = progressbar
		return GlossaryCommon.convertV2(self, ConvertArgs(
			inputFilename=inputFilename,
			inputFormat=inputFormat,
			direct=direct,
			outputFilename=outputFilename,
			outputFormat=outputFormat,
			sort=sort,
			sortKeyName=sortKeyName,
			sortEncoding=sortEncoding,
			readOptions=readOptions,
			writeOptions=writeOptions,
			sqlite=sqlite,
			infoOverride=infoOverride,
		))
