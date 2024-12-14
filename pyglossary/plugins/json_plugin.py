# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.compression import (
	# compressionOpen,
	stdCompressions,
)
from pyglossary.option import (
	BoolOption,
	EncodingOption,
	Option,
)

if TYPE_CHECKING:
	from collections.abc import Generator

	from pyglossary.glossary_types import (
		EntryType,
		GlossaryType,
	)

__all__ = [
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
lname = "json"
name = "Json"
description = "JSON (.json)"
extensions = (".json",)
extensionCreate = ".json"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/JSON"
website = (
	"https://www.json.org/json-en.html",
	"www.json.org",
)
optionsProp: dict[str, Option] = {
	"encoding": EncodingOption(),
	"enable_info": BoolOption(comment="Enable glossary info / metedata"),
	"resources": BoolOption(comment="Enable resources / data files"),
	"word_title": BoolOption(
		comment="add headwords title to beginning of definition",
	),
}


class Writer:
	_encoding: str = "utf-8"
	_enable_info: bool = True
	_resources: bool = True
	_word_title: bool = False

	compressions = stdCompressions

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		glos.preventDuplicateWords()

	def open(self, filename: str) -> None:
		self._filename = filename

	def finish(self) -> None:
		self._filename = ""

	def write(self) -> Generator[None, EntryType, None]:
		from json import dumps

		from pyglossary.text_writer import writeTxt

		glos = self._glos
		encoding = self._encoding
		enable_info = self._enable_info
		resources = self._resources

		ensure_ascii = encoding == "ascii"

		def escape(st: str) -> str:
			return dumps(st, ensure_ascii=ensure_ascii)

		yield from writeTxt(
			glos,
			entryFmt="\t{word}: {defi},\n",
			filename=self._filename,
			encoding=encoding,
			writeInfo=enable_info,
			wordEscapeFunc=escape,
			defiEscapeFunc=escape,
			ext=".json",
			head="{\n",
			tail='\t"": ""\n}',
			resources=resources,
			word_title=self._word_title,
		)
