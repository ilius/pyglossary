# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.compression import (
	# compressionOpen,
	stdCompressions,
)
from pyglossary.core import log
from pyglossary.file_utils import fileCountLines
from pyglossary.option import (
	BoolOption,
	EncodingOption,
	NewlineOption,
	Option,
)
from pyglossary.text_reader import TextGlossaryReader, nextBlockResultType
from pyglossary.text_utils import splitByBar

if TYPE_CHECKING:
	from collections.abc import Generator

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
lname = "lingoes_ldf"
name = "LingoesLDF"
description = "Lingoes Source (.ldf)"
extensions = (".ldf",)
extensionCreate = ".ldf"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/Lingoes"
website = (
	"http://www.lingoes.net/en/dictionary/dict_format.php",
	"Lingoes.net",
)
optionsProp: dict[str, Option] = {
	"newline": NewlineOption(),
	"resources": BoolOption(comment="Enable resources / data files"),
	"encoding": EncodingOption(),
}


class Reader(TextGlossaryReader):
	compressions = stdCompressions

	def __len__(self) -> int:
		if self._wordCount is None:
			log.debug("Try not to use len(reader) as it takes extra time")
			self._wordCount = (
				fileCountLines(
					self._filename,
					newline=b"\n\n",
				)
				- self._leadingLinesCount
			)
		return self._wordCount

	@classmethod
	def isInfoWord(cls, word: str) -> bool:
		if isinstance(word, str):
			return word.startswith("#")

		return False

	@classmethod
	def fixInfoWord(cls, word: str) -> str:
		if isinstance(word, str):
			return word.lstrip("#").lower()

		return word

	def nextBlock(self) -> nextBlockResultType:
		if not self._file:
			raise StopIteration
		entryLines: list[str] = []
		while True:
			line = self.readline()
			if not line:
				raise StopIteration
			line = line.rstrip("\n\r")  # FIXME
			if line.startswith("###"):
				parts = line.split(":")
				key = parts[0].strip()
				value = ":".join(parts[1:]).strip()
				return key, value, None

			if line:
				entryLines.append(line)
				continue

			# now `line` is empty, process `entryLines`
			if not entryLines:
				return None
			if len(entryLines) < 2:
				log.error(
					f"invalid block near pos {self._file.tell()}"
					f" in file {self._filename}",
				)
				return None
			word = entryLines[0]
			defi = "\n".join(entryLines[1:])
			defi = defi.replace("<br/>", "\n")  # FIXME

			words = splitByBar(word)

			return words, defi, None


class Writer:
	compressions = stdCompressions

	_newline: str = "\n"
	_resources: bool = True

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = ""

	def getInfo(self, key: str) -> str:
		return self._glos.getInfo(key).replace("\n", "<br>")

	def getAuthor(self) -> str:
		return self._glos.author.replace("\n", "<br>")

	def finish(self) -> None:
		self._filename = ""

	def open(self, filename: str) -> None:
		self._filename = filename

	@staticmethod
	def _defiEscapeFunc(defi: str) -> str:
		return defi.replace("\n", "<br/>")

	def write(self) -> Generator[None, EntryType, None]:
		from pyglossary.text_writer import writeTxt

		newline = self._newline
		resources = self._resources
		head = (
			f"###Title: {self.getInfo('title')}\n"
			f"###Description: {self.getInfo('description')}\n"
			f"###Author: {self.getAuthor()}\n"
			f"###Email: {self.getInfo('email')}\n"
			f"###Website: {self.getInfo('website')}\n"
			f"###Copyright: {self.getInfo('copyright')}\n"
		)
		yield from writeTxt(
			self._glos,
			entryFmt="{word}\n{defi}\n\n",
			filename=self._filename,
			writeInfo=False,
			defiEscapeFunc=self._defiEscapeFunc,
			ext=".ldf",
			head=head,
			newline=newline,
			resources=resources,
		)
