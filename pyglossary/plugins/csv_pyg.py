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

from formats_common import *
import csv


enable = True
lname = "csv"
format = "Csv"
description = "CSV (.csv)"
extensions = (".csv",)
extensionCreate = ".csv"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/Comma-separated_values"
website = None

optionsProp = {
	"encoding": EncodingOption(),
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
		comment="add headwords title to begining of definition",
	),
}


class Reader(object):
	compressions = stdCompressions

	_encoding: str = "utf-8"
	_delimiter: str = ","

	def __init__(self, glos: GlossaryType):
		self._glos = glos
		self.clear()

	def clear(self) -> None:
		self._filename = ""
		self._file = None
		self._leadingLinesCount = 0
		self._wordCount = None
		self._pos = -1
		self._csvReader = None
		self._resDir = ""
		self._resFileNames = []
		self._bufferRow = None

	def open(
		self,
		filename: str,
	) -> None:
		from pyglossary.text_reader import TextFilePosWrapper
		self._filename = filename
		cfile = compressionOpen(filename, mode="rt", encoding=self._encoding)
		cfile.seek(0, 2)
		self._fileSize = cfile.tell()
		cfile.seek(0)
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
			self._wordCount = fileCountLines(self._filename) - \
				self._leadingLinesCount
		return self._wordCount + len(self._resFileNames)

	def _iterRows(self):
		if self._bufferRow:
			yield self._bufferRow
		for row in self._csvReader:
			yield row

	def __iter__(self) -> "Iterator[BaseEntry]":
		if not self._csvReader:
			raise RuntimeError("iterating over a reader while it's not open")

		wordCount = 0
		for row in self._iterRows():
			wordCount += 1
			if not row:
				yield None  # update progressbar
				continue
			try:
				word = row[0]
				defi = row[1]
			except IndexError:
				log.error(f"invalid row: {row!r}")
				yield None  # update progressbar
				continue
			try:
				alts = row[2].split(",")
			except IndexError:
				pass
			else:
				word = [word] + alts
			yield self._glos.newEntry(
				word,
				defi,
				byteProgress=(self._file.tell(), self._fileSize),
			)
		self._wordCount = wordCount

		resDir = self._resDir
		for fname in self._resFileNames:
			with open(join(resDir, fname), "rb") as fromFile:
				yield self._glos.newDataEntry(
					fname,
					fromFile.read(),
				)


class Writer(object):
	compressions = stdCompressions

	_encoding: str = "utf-8"
	_resources: bool = True
	_delimiter: str = ","
	_add_defi_format: bool = False
	_enable_info: bool = True
	_word_title: bool = False

	def __init__(self, glos: GlossaryType):
		self._glos = glos

	def open(self, filename: str):
		self._filename = filename
		self._file = compressionOpen(filename, mode="wt", encoding=self._encoding)
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

	def finish(self):
		self._filename = None
		if self._file:
			self._file.close()
			self._file = None
		if not os.listdir(self._resDir):
			os.rmdir(self._resDir)

	def write(self) -> "Generator[None, BaseEntry, None]":
		encoding = self._encoding
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
