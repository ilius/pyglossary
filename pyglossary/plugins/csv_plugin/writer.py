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
from os.path import isdir
from typing import TYPE_CHECKING, cast

from pyglossary.compression import (
	compressionOpen,
	stdCompressions,
)
from pyglossary.io_utils import nullTextIO

if TYPE_CHECKING:
	import io
	from collections.abc import Generator

	from pyglossary.glossary_types import EntryType, WriterGlossaryType

__all__ = ["Writer"]


class Writer:
	compressions = stdCompressions

	_encoding: str = "utf-8"
	_newline: str = "\n"
	_resources: bool = True
	_delimiter: str = ","
	_add_defi_format: bool = False
	_enable_info: bool = True
	_word_title: bool = False

	def __init__(self, glos: WriterGlossaryType) -> None:
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
