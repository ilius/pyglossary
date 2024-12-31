# -*- coding: utf-8 -*-

from __future__ import annotations

import os
from os.path import isdir
from typing import TYPE_CHECKING

from pyglossary.core import exc_note, log, pip
from pyglossary.io_utils import nullTextIO
from pyglossary.option import (
	BoolOption,
	Option,
)
from pyglossary.text_utils import splitByBar

if TYPE_CHECKING:
	import io
	from collections.abc import Generator, Iterator

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
lname = "gettext_po"
name = "GettextPo"
description = "Gettext Source (.po)"
extensions = (".po",)
extensionCreate = ".po"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/Gettext"
website = (
	"https://www.gnu.org/software/gettext",
	"gettext - GNU Project",
)
optionsProp: dict[str, Option] = {
	"resources": BoolOption(comment="Enable resources / data files"),
}


class Reader:
	depends = {
		"polib": "polib",
	}

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._alts = glos.alts
		self.clear()

	def clear(self) -> None:
		self._filename = ""
		self._file: io.TextIOBase = nullTextIO
		self._wordCount: int | None = None
		self._resDir = ""
		self._resFileNames: list[str] = []

	def open(self, filename: str) -> None:
		self._filename = filename
		self._file = open(filename, encoding="utf-8")
		self._resDir = filename + "_res"
		if isdir(self._resDir):
			self._resFileNames = os.listdir(self._resDir)
		else:
			self._resDir = ""
			self._resFileNames = []

	def close(self) -> None:
		self._file.close()
		self._file = nullTextIO
		self.clear()

	def __len__(self) -> int:
		from pyglossary.file_utils import fileCountLines

		if self._wordCount is None:
			log.debug("Try not to use len(reader) as it takes extra time")
			self._wordCount = fileCountLines(
				self._filename,
				newline=b"\nmsgid",
			)
		return self._wordCount

	def makeEntry(self, word: str, defi: str) -> EntryType:
		if self._alts:
			return self._glos.newEntry(splitByBar(word), defi)
		return self._glos.newEntry(word, defi)

	def __iter__(self) -> Iterator[EntryType]:  # noqa: PLR0912
		try:
			from polib import unescape as po_unescape
		except ModuleNotFoundError as e:
			exc_note(e, f"Run `{pip} install polib` to install")
			raise

		file = self._file

		word = ""
		defi = ""
		msgstr = False
		wordCount = 0
		for line_ in file:
			line = line_.strip()  # noqa: PLW2901
			if not line:
				continue
			if line.startswith("#"):
				continue
			if line.startswith("msgid "):
				if word:
					yield self.makeEntry(word, defi)
					wordCount += 1
					word = ""
					defi = ""
				else:
					pass
					# TODO: parse defi and set glos info?
					# but this should be done in self.open
				word = po_unescape(line[6:])
				if word.startswith('"'):
					if len(word) < 2 or word[-1] != '"':
						raise ValueError("invalid po line: line")
					word = word[1:-1]
				msgstr = False
				continue
			if line.startswith("msgstr "):
				if msgstr:
					log.error("msgid omitted!")
				defi = po_unescape(line[7:])
				if defi.startswith('"'):
					if len(defi) < 2 or defi[-1] != '"':
						raise ValueError("invalid po line: line")
					defi = defi[1:-1]
				msgstr = True
				continue

			line = po_unescape(line)
			if line.startswith('"'):
				if len(line) < 2 or line[-1] != '"':
					raise ValueError("invalid po line: line")
				line = line[1:-1]

			if msgstr:
				defi += line
			else:
				word += line
		if word:
			yield self.makeEntry(word, defi)
			wordCount += 1
		self._wordCount = wordCount


class Writer:
	depends = {
		"polib": "polib",
	}

	_resources: bool = True

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._file: io.TextIOBase = nullTextIO
		glos.preventDuplicateWords()

	def open(self, filename: str) -> None:
		try:
			from polib import escape as po_escape
		except ModuleNotFoundError as e:
			exc_note(e, f"Run `{pip} install polib` to install")
			raise

		self._filename = filename
		self._file = file = open(filename, mode="w", encoding="utf-8")
		file.write('#\nmsgid ""\nmsgstr ""\n')
		for key, value in self._glos.iterInfo():
			file.write(f'"{po_escape(key)}: {po_escape(value)}\\n"\n')

	def finish(self) -> None:
		self._filename = ""
		self._file.close()
		self._file = nullTextIO

	def write(self) -> Generator[None, EntryType, None]:
		from polib import escape as po_escape

		file = self._file

		resources = self._resources
		filename = self._filename
		while True:
			entry = yield
			if entry is None:
				break
			if entry.isData():
				if resources:
					entry.save(filename + "_res")
				continue
			file.write(
				f'msgid "{po_escape(entry.s_word)}"\n'
				f'msgstr "{po_escape(entry.defi)}"\n\n',
			)
