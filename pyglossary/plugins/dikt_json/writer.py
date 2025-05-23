# -*- coding: utf-8 -*-
# mypy: ignore-errors
# from https://github.com/maxim-saplin/pyglossary

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pyglossary.compression import stdCompressions

if TYPE_CHECKING:
	from collections.abc import Generator

	from pyglossary.glossary_types import EntryType, WriterGlossaryType

__all__ = ["Writer"]


class Writer:
	_encoding: str = "utf-8"
	_enable_info: bool = True
	_resources: bool = True
	_word_title: bool = False

	compressions = stdCompressions

	def __init__(self, glos: WriterGlossaryType) -> None:
		self._glos = glos
		self._filename = None
		glos.preventDuplicateWords()

	def open(self, filename: str) -> None:
		self._filename = filename

	def finish(self) -> None:
		self._filename = None

	def write(self) -> Generator[None, EntryType, None]:
		from json import dumps

		from pyglossary.text_writer import writeTxt

		glos = self._glos
		encoding = self._encoding
		enable_info = self._enable_info
		resources = self._resources

		ensure_ascii = encoding == "ascii"

		def escape(st: str) -> str:
			# remove styling from HTML tags
			st2 = re.sub(r' style="[^"]*"', "", st)
			st2 = re.sub(r' class="[^"]*"', "", st2)
			st2 = re.sub(r"<font [^>]*>", "", st2)
			st2 = st2.replace("</font>", "")
			st2 = re.sub(r"\n", "", st2)
			st2 = st2.replace("<div></div>", "")
			st2 = st2.replace("<span></span>", "")
			# fix russian dictionary issues,
			# such as hyphenation in word (e.g. абб{[']}а{[/']}т)
			st2 = re.sub(r"\{\['\]\}", "", st2)
			st2 = re.sub(r"\{\[/'\]\}", "", st2)
			return dumps(st2, ensure_ascii=ensure_ascii)

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
