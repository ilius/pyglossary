# -*- coding: utf-8 -*-
#
# Copyright © 2013-2019 Saeed Rasooli <saeed.gnu@gmail.com> (ilius)
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

import csv
from os.path import isdir, join
from typing import TYPE_CHECKING, cast

from pyglossary.compress import (
	compressionOpen,
	stdCompressions,
)
from pyglossary.core import log
from pyglossary.io_utils import nullTextIO
from pyglossary.os_utils import listFilesRecursiveRelPath

if TYPE_CHECKING:
	import io
	from collections.abc import Iterable, Iterator

	from pyglossary.glossary_types import EntryType, ReaderGlossaryType

__all__ = ["Reader"]


class Reader:
	useByteProgress = True
	compressions = stdCompressions

	_encoding: str = "utf-8"
	_newline: str = "\n"
	_delimiter: str = ","

	def __init__(self, glos: ReaderGlossaryType) -> None:
		self._glos = glos
		self.clear()

	def clear(self) -> None:
		self._filename = ""
		self._file: io.TextIOBase = nullTextIO
		self._fileSize = 0
		self._leadingLinesCount = 0
		self._entryCount: int | None = None
		self._pos = -1
		self._csvReader: Iterable[list[str]] | None = None
		self._resDir = ""
		self._bufferRow: list[str] | None = None

	def open(
		self,
		filename: str,
	) -> None:
		from pyglossary.text_reader import TextFilePosWrapper

		self._filename = filename
		cfile = cast(
			"io.TextIOBase",
			compressionOpen(
				filename,
				mode="rt",
				encoding=self._encoding,
				newline=self._newline,
			),
		)

		if self._glos.progressbar:
			if cfile.seekable():
				cfile.seek(0, 2)
				self._fileSize = cfile.tell()
				cfile.seek(0)
				# self._glos.setInfo("input_file_size", f"{self._fileSize}")
			else:
				log.warning("CSV Reader: file is not seekable")

		self._file = TextFilePosWrapper(cfile, self._encoding)
		self._csvReader = csv.reader(
			self._file,
			dialect="excel",
			delimiter=self._delimiter,
		)
		self._resDir = filename + "_res"
		resCount = 0
		if not isdir(self._resDir):
			self._resDir = ""
		elif self._glos.progressbar:
			log.info("Counting resource files...")
			resCount = sum(1 for _f in listFilesRecursiveRelPath(self._resDir))
			log.info(f"Found {resCount} resource files")
		self._resCount = resCount

		for row in self._csvReader:
			if not row:
				continue
			if not row[0].startswith("#"):
				self._bufferRow = row
				break
			if len(row) < 2:
				log.error(f"invalid row: {row}")
				continue
			self._glos.setInfo(row[0].lstrip("#"), row[1])

	def close(self) -> None:
		if self._file:
			try:
				self._file.close()
			except Exception:
				log.exception("error while closing csv file")
		self.clear()

	def countResourceFiles(self) -> int:
		return self._resCount

	def __len__(self) -> int:
		from pyglossary.file_utils import fileCountLines

		if self._entryCount is not None:
			return self._entryCount

		if hasattr(self._file, "compression"):
			return 0

		self._entryCount = (
			fileCountLines(self._filename) - self._leadingLinesCount + self._resCount
		)
		return self._entryCount

	def _iterRows(self) -> Iterator[list[str]]:
		if self._csvReader is None:
			raise RuntimeError("self._csvReader is None")
		if self._bufferRow:
			yield self._bufferRow
		yield from self._csvReader

	def _processRow(self, row: list[str]) -> EntryType | None:
		if not row:
			return None

		term: str | list[str]
		try:
			term = row[0]
			defi = row[1]
		except IndexError:
			log.error(f"invalid row: {row!r}")
			return None

		try:
			alts = row[2].split(",")
		except IndexError:
			pass
		else:
			term = [term] + alts

		return self._glos.newEntry(
			term,
			defi,
			byteProgress=(
				(self._file.tell(), self._fileSize) if self._fileSize else None
			),
		)

	def __iter__(self) -> Iterator[EntryType | None]:
		if not self._csvReader:
			raise RuntimeError("iterating over a reader while it's not open")

		entryCount = 0
		for row in self._iterRows():
			entryCount += 1
			yield self._processRow(row)

		resDir = self._resDir
		for fname in listFilesRecursiveRelPath(resDir):
			with open(join(resDir, fname), "rb") as file:
				entryCount += 1
				yield self._glos.newDataEntry(
					fname,
					file.read(),
				)

		self._entryCount = entryCount
