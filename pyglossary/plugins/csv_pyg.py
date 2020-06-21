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
from pyglossary.file_utils import fileCountLines


enable = True
format = "Csv"
description = "CSV"
extensions = [".csv"]
optionsProp = {
	"encoding": EncodingOption(),
	"resources": BoolOption(),
}
depends = {}
supportsAlternates = True


class Reader(object):
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

	def open(self, filename: str, encoding: str = "utf-8") -> None:
		self._filename = filename
		self._file = open(filename, "r", encoding=encoding)
		self._csvReader = csv.reader(
			self._file,
			dialect="excel",
		)
		self._resDir = filename + "_res"
		if isdir(self._resDir):
			self._resFileNames = os.listdir(self._resDir)
		else:
			self._resDir = ""
			self._resFileNames = []

	def close(self) -> None:
		if self._file:
			try:
				self._file.close()
			except:
				log.exception("error while closing csv file")
		self.clear()

	def __len__(self) -> int:
		if self._wordCount is None:
			log.debug("Try not to use len(reader) as it takes extra time")
			self._wordCount = fileCountLines(self._filename) - \
				self._leadingLinesCount
		return self._wordCount + len(self._resFileNames)

	def __iter__(self) -> Iterator[BaseEntry]:
		if not self._csvReader:
			log.error(f"{self} is not open, can not iterate")
			raise StopIteration

		wordCount = 0
		for row in self._csvReader:
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
			yield self._glos.newEntry(word, defi)
		self._wordCount = wordCount

		resDir = self._resDir
		for fname in self._resFileNames:
			with open(join(resDir, fname), "rb") as fromFile:
				yield self._glos.newDataEntry(
					fname,
					fromFile.read(),
				)


def write(glos: GlossaryType, filename: str, encoding: str = "utf-8", resources: bool = True) -> None:
	resDir = filename + "_res"
	if not isdir(resDir):
		os.mkdir(resDir)
	with open(filename, "w", encoding=encoding) as csvfile:
		writer = csv.writer(
			csvfile,
			dialect="excel",
			quoting=csv.QUOTE_ALL,  # FIXME
		)
		for entry in glos:
			if entry.isData():
				if resources:
					entry.save(resDir)
				continue

			words = entry.getWords()
			if not words:
				continue
			word, alts = words[0], words[1:]
			defi = entry.getDefi()

			row = [
				word,
				defi,
			]
			if alts:
				row.append(",".join(alts))

			writer.writerow(row)

	if not os.listdir(resDir):
		os.rmdir(resDir)
