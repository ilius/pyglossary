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
from __future__ import annotations

import warnings
from os.path import relpath
from time import perf_counter as now
from typing import TYPE_CHECKING

from .core import log
from .glossary_v2 import ConvertArgs, Error, GlossaryCommon, ReadError, WriteError
from .sort_keys import lookupSortKey

if TYPE_CHECKING:
	from typing import Any

	from .glossary_types import EntryType
	from .plugin_manager import DetectedFormat
	from .ui_type import UIType


__all__ = ["Glossary"]


class Glossary(GlossaryCommon):
	GLOSSARY_API_VERSION = "1.0"

	def __init__(
		self,
		info: dict[str, str] | None = None,
		ui: UIType | None = None,  # noqa: F821
	) -> None:
		"""
		info: dict instance, or None
		no need to copy dict instance before passing here
		we will not reference to it.
		"""
		warnings.warn(
			"This class is deprecated. Use glossary_v2.Glossary",
			category=DeprecationWarning,
			stacklevel=2,
		)
		GlossaryCommon.__init__(self, ui=ui)
		if info:
			if not isinstance(info, dict):
				raise TypeError(
					"Glossary: `info` has invalid type"
					", dict or OrderedDict expected",
				)
			for key, value in info.items():
				self.setInfo(key, value)

	def titleElement(  # noqa: ANN201
		self,
		hf,  # noqa: ANN001, type: ignore
		sample: str = "",
	):  # type: ignore
		return hf.element(self.titleTag(sample))

	def read(
		self,
		filename: str,
		direct: bool = False,
		progressbar: bool = True,
		**kwargs,  # noqa: ANN003
	) -> bool:
		"""
		Read from a given glossary file.

		Parameters
		----------
		filename (str):	name/path of input file
		formatName or format (str):	name of input format,
						or "" to detect from file extension
		direct (bool):	enable direct mode
		progressbar (bool): enable progressbar.

		read-options can be passed as additional keyword arguments

		"""
		if type(filename) is not str:
			raise TypeError("filename must be str")

		# don't allow direct=False when there are readers
		# (read is called before with direct=True)
		if self._readers and not direct:
			raise ValueError(
				f"there are already {len(self._readers)} readers"
				", you can not read with direct=False mode",
			)

		self._setTmpDataDir(filename)

		self._progressbar = progressbar

		return self._read(
			filename=filename,
			direct=direct,
			**kwargs,
		)

	def addEntryObj(self, entry: EntryType) -> None:
		self._data.append(entry)

	@staticmethod
	def updateIter() -> None:
		log.warning("calling glos.updateIter() is no longer needed.")

	def sortWords(
		self,
		sortKeyName: str = "headword_lower",
		sortEncoding: str = "utf-8",
		writeOptions: dict[str, Any] | None = None,
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

	@classmethod
	def detectInputFormat(  # type: ignore # pyright: ignore[reportIncompatibleMethodOverride]
		cls,
		*args,
		**kwargs,
	) -> DetectedFormat | None:
		try:
			return GlossaryCommon.detectInputFormat(*args, **kwargs)
		except Error as e:
			log.critical(str(e))
			return None

	@classmethod
	def detectOutputFormat(  # type: ignore # pyright: ignore[reportIncompatibleMethodOverride]
		cls,
		*args,
		**kwargs,
	) -> DetectedFormat | None:
		try:
			return GlossaryCommon.detectOutputFormat(*args, **kwargs)
		except Error as e:
			log.critical(str(e))
			return None

	def convert(  # noqa: PLR0913
		self,
		inputFilename: str,
		inputFormat: str = "",
		direct: bool | None = None,
		progressbar: bool = True,
		outputFilename: str = "",
		outputFormat: str = "",
		sort: bool | None = None,
		sortKeyName: str | None = None,
		sortEncoding: str | None = None,
		readOptions: dict[str, Any] | None = None,
		writeOptions: dict[str, Any] | None = None,
		sqlite: bool | None = None,
		infoOverride: dict[str, str] | None = None,
	) -> str | None:
		self.progressbar = progressbar
		try:
			return GlossaryCommon.convertV2(
				self,
				ConvertArgs(
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
				),
			)
		except ReadError as e:
			log.critical(str(e))
			log.critical(f"Reading file {relpath(inputFilename)!r} failed.")
		except WriteError as e:
			log.critical(str(e))
			log.critical(f"Writing file {relpath(outputFilename)!r} failed.")
		except Error as e:
			log.critical(str(e))

		self.cleanup()
		return None
