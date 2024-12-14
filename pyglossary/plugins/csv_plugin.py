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
import os
from os.path import isdir, join
from typing import TYPE_CHECKING, cast

from pyglossary.compression import (
	compressionOpen,
	stdCompressions,
)
from pyglossary.core import log
from pyglossary.io_utils import nullTextIO
from pyglossary.option import (
	BoolOption,
	EncodingOption,
	NewlineOption,
	Option,
)

if TYPE_CHECKING:
	import io
	from collections.abc import Generator, Iterable, Iterator

	from pyglossary.glossary_types import EntryType, GlossaryType

__all__ = [
	"Reader",
	"Writer",
	"description",
	"enable",
	"extensionCreate",
	"extensions",
	"kind",
	"lname",
	"name",
	"optionsProp",
	"singleFile",
	"website",
	"wiki",
]

enable = True
lname = "csv"
name = "Csv"
description = "CSV (.csv)"
extensions = (".csv",)
extensionCreate = ".csv"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/Comma-separated_values"
website = None

optionsProp: dict[str, Option] = {
	"encoding": EncodingOption(),
	"newline": NewlineOption(),
	"resources": BoolOption(
		comment="Enable resources / data files",
	),
	"delimiter": Option(
		typ="str",
		customValue=True,
		values=[",", ";", "@"],
		comment="Column delimiter",
	),
	"add_defi_format": BoolOption(
		comment="enable adding defiFormat (m/h/x)",
	),
	"enable_info": BoolOption(
		comment="Enable glossary info / metedata",
	),
	"word_title": BoolOption(
		comment="add headwords title to beginning of definition",
	),
}

csv.field_size_limit(0x7FFFFFFF)


class Reader:
	compressions = stdCompressions

	_encoding: str = "utf-8"
	_newline: str = "\n"
	_delimiter: str = ","

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self.clear()

	def clear(self) -> None:
		self._filename = ""
		self._file: io.TextIOBase = nullTextIO
		self._fileSize = 0
		self._leadingLinesCount = 0
		self._wordCount: int | None = None
		self._pos = -1
		self._csvReader: Iterable[list[str]] | None = None
		self._resDir = ""
		self._resFileNames: list[str] = []
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
		if isdir(self._resDir):
			self._resFileNames = os.listdir(self._resDir)
		else:
			self._resDir = ""
			self._resFileNames = []
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

	def __len__(self) -> int:
		from pyglossary.file_utils import fileCountLines

		if self._wordCount is None:
			if hasattr(self._file, "compression"):
				return 0
			log.debug("Try not to use len(reader) as it takes extra time")
			self._wordCount = fileCountLines(self._filename) - self._leadingLinesCount
		return self._wordCount + len(self._resFileNames)

	def _iterRows(self) -> Iterator[list[str]]:
		if self._csvReader is None:
			raise RuntimeError("self._csvReader is None")
		if self._bufferRow:
			yield self._bufferRow
		yield from self._csvReader

	def _processRow(self, row: list[str]) -> EntryType | None:
		if not row:
			return None

		word: str | list[str]
		try:
			word = row[0]
			defi = row[1]
		except IndexError:
			log.error(f"invalid row: {row!r}")
			return None

		try:
			alts = row[2].split(",")
		except IndexError:
			pass
		else:
			word = [word] + alts

		return self._glos.newEntry(
			word,
			defi,
			byteProgress=(
				(self._file.tell(), self._fileSize) if self._fileSize else None
			),
		)

	def __iter__(self) -> Iterator[EntryType | None]:
		if not self._csvReader:
			raise RuntimeError("iterating over a reader while it's not open")

		wordCount = 0
		for row in self._iterRows():
			wordCount += 1
			yield self._processRow(row)

		self._wordCount = wordCount

		resDir = self._resDir
		for fname in self._resFileNames:
			with open(join(resDir, fname), "rb") as _file:
				yield self._glos.newDataEntry(
					fname,
					_file.read(),
				)


class Writer:
	compressions = stdCompressions

	_encoding: str = "utf-8"
	_newline: str = "\n"
	_resources: bool = True
	_delimiter: str = ","
	_add_defi_format: bool = False
	_enable_info: bool = True
	_word_title: bool = False

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._file: io.TextIOBase = nullTextIO

	def open(self, filename: str) -> None:
		self._filename = filename
		self._file = cast(
			"io.TextIOBase",
			compressionOpen(
				filename,
				mode="wt",
				encoding=self._encoding,
				newline=self._newline,
			),
		)
		self._resDir = resDir = filename + "_res"
		self._csvWriter = csv.writer(
			self._file,
			dialect="excel",
			quoting=csv.QUOTE_ALL,  # FIXME
			delimiter=self._delimiter,
		)
		if not isdir(resDir):
			os.mkdir(resDir)
		if self._enable_info:
			for key, value in self._glos.iterInfo():
				self._csvWriter.writerow([f"#{key}", value])

	def finish(self) -> None:
		self._filename = ""
		self._file.close()
		self._file = nullTextIO
		if not os.listdir(self._resDir):
			os.rmdir(self._resDir)

	def write(self) -> Generator[None, EntryType, None]:
		resources = self._resources
		add_defi_format = self._add_defi_format
		glos = self._glos
		resDir = self._resDir
		writer = self._csvWriter
		word_title = self._word_title
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				if resources:
					entry.save(resDir)
				continue

			words = entry.l_word
			if not words:
				continue
			word, alts = words[0], words[1:]
			defi = entry.defi

			if word_title:
				defi = glos.wordTitleStr(words[0]) + defi

			row = [
				word,
				defi,
			]
			if add_defi_format:
				entry.detectDefiFormat()
				row.append(entry.defiFormat)
			if alts:
				row.append(",".join(alts))

			writer.writerow(row)
