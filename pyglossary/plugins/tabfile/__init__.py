# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.compression import stdCompressions
from pyglossary.core import log
from pyglossary.option import (
	BoolOption,
	EncodingOption,
	FileSizeOption,
	Option,
)
from pyglossary.text_reader import TextGlossaryReader
from pyglossary.text_utils import (
	splitByBarUnescapeNTB,
	unescapeNTB,
)

if TYPE_CHECKING:
	from collections.abc import Generator

	from pyglossary.glossary_types import EntryType, GlossaryType

__all__ = ["Reader"]

enable = True
lname = "tabfile"
name = "Tabfile"
description = "Tabfile (.txt, .dic)"
extensions = (".txt", ".tab", ".tsv")
extensionCreate = ".txt"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/Tab-separated_values"
website = None
optionsProp: dict[str, Option] = {
	"encoding": EncodingOption(),
	"enable_info": BoolOption(
		comment="Enable glossary info / metedata",
	),
	"resources": BoolOption(
		comment="Enable resources / data files",
	),
	"file_size_approx": FileSizeOption(
		comment="Split up by given approximate file size\nexamples: 100m, 1g",
	),
	"word_title": BoolOption(
		comment="Add headwords title to beginning of definition",
	),
}


class Reader(TextGlossaryReader):
	@classmethod
	def isInfoWord(cls, word: str) -> bool:
		return word.startswith("#")

	@classmethod
	def fixInfoWord(cls, word: str) -> str:
		return word.lstrip("#")

	def nextBlock(self) -> tuple[str | list[str], str, None] | None:
		if not self._file:
			raise StopIteration
		line = self.readline()
		if not line:
			raise StopIteration
		line = line.rstrip("\n")
		if not line:
			return None
		###
		word: str | list[str]
		word, tab, defi = line.partition("\t")
		if not tab:
			log.warning(
				f"Warning: line starting with {line[:10]!r} has no tab!",
			)
			return None
		###
		if self._glos.alts:
			word = splitByBarUnescapeNTB(word)
			if len(word) == 1:
				word = word[0]
		else:
			word = unescapeNTB(word, bar=False)
		###
		defi = unescapeNTB(defi)
		###
		return word, defi, None


class Writer:
	_encoding: str = "utf-8"
	_enable_info: bool = True
	_resources: bool = True
	_file_size_approx: int = 0
	_word_title: bool = False

	compressions = stdCompressions

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = ""

	def open(
		self,
		filename: str,
	) -> None:
		self._filename = filename

	def finish(self) -> None:
		pass

	def write(self) -> Generator[None, EntryType, None]:
		from pyglossary.text_utils import escapeNTB, joinByBar
		from pyglossary.text_writer import TextGlossaryWriter

		writer = TextGlossaryWriter(
			self._glos,
			entryFmt="{word}\t{defi}\n",
			writeInfo=self._enable_info,
			outInfoKeysAliasDict=None,
		)
		writer.setAttrs(
			encoding=self._encoding,
			wordListEncodeFunc=joinByBar,
			wordEscapeFunc=escapeNTB,
			defiEscapeFunc=escapeNTB,
			ext=".txt",
			resources=self._resources,
			word_title=self._word_title,
			file_size_approx=self._file_size_approx,
		)
		writer.open(self._filename)
		yield from writer.write()
		writer.finish()
