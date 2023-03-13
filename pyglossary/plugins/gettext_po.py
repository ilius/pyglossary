# -*- coding: utf-8 -*-

import io
import os
import typing
from os.path import isdir
from typing import Generator, Iterator

from pyglossary.core import log, pip
from pyglossary.glossary_types import EntryType, GlossaryType
from pyglossary.option import (
	BoolOption,
	Option,
)

enable = True
lname = "gettext_po"
format = "GettextPo"
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
optionsProp: "dict[str, Option]" = {
	"resources": BoolOption(comment="Enable resources / data files"),
}


class Reader(object):
	depends = {
		"polib": "polib",
	}

	def __init__(self: "typing.Self", glos: GlossaryType) -> None:
		self._glos = glos
		self.clear()

	def clear(self: "typing.Self") -> None:
		self._filename = ""
		self._file: "io.TextIOBase | None" = None
		self._wordCount: "int | None" = None
		self._resDir = ""
		self._resFileNames: "list[str]" = []

	def open(self: "typing.Self", filename: str) -> None:
		self._filename = filename
		self._file = open(filename)
		self._resDir = filename + "_res"
		if isdir(self._resDir):
			self._resFileNames = os.listdir(self._resDir)
		else:
			self._resDir = ""
			self._resFileNames = []

	def close(self: "typing.Self") -> None:
		if self._file:
			self._file.close()
		self.clear()

	def __len__(self: "typing.Self") -> int:
		from pyglossary.file_utils import fileCountLines
		if self._wordCount is None:
			log.debug("Try not to use len(reader) as it takes extra time")
			self._wordCount = fileCountLines(
				self._filename,
				newline=b"\nmsgid",
			)
		return self._wordCount

	def __iter__(self: "typing.Self") -> "Iterator[EntryType]":
		try:
			from polib import unescape as po_unescape
		except ModuleNotFoundError as e:
			e.msg += f", run `{pip} install polib` to install"
			raise e
		
		_file = self._file
		if _file is None:
			raise ValueError("_file is None")
		
		word = ""
		defi = ""
		msgstr = False
		wordCount = 0
		for line in _file:
			line = line.strip()
			if not line:
				continue
			if line.startswith("#"):
				continue
			if line.startswith("msgid "):
				if word:
					yield self._glos.newEntry(word, defi)
					wordCount += 1
					word = ""
					defi = ""
				else:
					pass
					# TODO: parse defi and set glos info?
					# but this should be done in self.open
				word = po_unescape(line[6:])
				msgstr = False
			elif line.startswith("msgstr "):
				if msgstr:
					log.error("msgid omitted!")
				defi = po_unescape(line[7:])
				msgstr = True
			else:
				if msgstr:
					defi += po_unescape(line)
				else:
					word += po_unescape(line)
		if word:
			yield self._glos.newEntry(word, defi)
			wordCount += 1
		self._wordCount = wordCount


class Writer(object):
	depends = {
		"polib": "polib",
	}

	_resources: bool = True

	def __init__(self: "typing.Self", glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._file: "io.TextIOBase | None" = None

	def open(self: "typing.Self", filename: str) -> None:
		self._filename = filename
		self._file = _file = open(filename, mode="wt", encoding="utf-8")
		_file.write('#\nmsgid ""\nmsgstr ""\n')
		for key, value in self._glos.iterInfo():
			_file.write(f'"{key}: {value}\\n"\n')

	def finish(self: "typing.Self") -> None:
		self._filename = ""
		if self._file:
			self._file.close()
			self._file = None

	def write(self: "typing.Self") -> "Generator[None, EntryType, None]":
		try:
			from polib import escape as po_escape
		except ModuleNotFoundError as e:
			e.msg += f", run `{pip} install polib` to install"
			raise e

		_file = self._file
		if _file is None:
			raise ValueError("_file is None")

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
			_file.write(
				f"msgid {po_escape(entry.s_word)}\n"
				f"msgstr {po_escape(entry.defi)}\n\n",
			)
