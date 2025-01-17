# -*- coding: utf-8 -*-

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from pyglossary.core import log
from pyglossary.plugin_lib.dictdlib import DictDB

if TYPE_CHECKING:
	from collections.abc import Iterator

	from pyglossary.glossary_types import EntryType, ReaderGlossaryType

__all__ = ["Reader"]


class Reader:
	useByteProgress = False

	def __init__(self, glos: ReaderGlossaryType) -> None:
		self._glos = glos
		self._filename = ""
		self._dictdb: DictDB | None = None

		# regular expression patterns used to prettify definition text
		self._re_newline_in_braces = re.compile(
			r"\{(?P<left>.*?)\n(?P<right>.*?)?\}",
		)
		self._re_words_in_braces = re.compile(
			r"\{(?P<word>.+?)\}",
		)

	def open(self, filename: str) -> None:
		filename = filename.removesuffix(".index")
		self._filename = filename
		self._dictdb = DictDB(filename, "read", 1)

	def close(self) -> None:
		if self._dictdb is not None:
			self._dictdb.close()
			# self._dictdb.finish()
			self._dictdb = None

	def prettifyDefinitionText(self, defi: str) -> str:
		# Handle words in {}
		# First, we remove any \n in {} pairs
		defi = self._re_newline_in_braces.sub(r"{\g<left>\g<right>}", defi)

		# Then, replace any {words} into <a href="bword://words">words</a>,
		# so it can be rendered as link correctly
		defi = self._re_words_in_braces.sub(
			r'<a href="bword://\g<word>">\g<word></a>',
			defi,
		)

		# Use <br /> so it can be rendered as newline correctly
		return defi.replace("\n", "<br />")

	def __len__(self) -> int:
		if self._dictdb is None:
			return 0
		return len(self._dictdb)

	def __iter__(self) -> Iterator[EntryType]:
		if self._dictdb is None:
			raise RuntimeError("iterating over a reader while it's not open")
		dictdb = self._dictdb
		for word in dictdb.getDefList():
			b_defi = b"\n\n<hr>\n\n".join(dictdb.getDef(word))
			try:
				defi = b_defi.decode("utf_8", "ignore")
				defi = self.prettifyDefinitionText(defi)
			except Exception as e:
				log.error(f"{b_defi = }")
				raise e
			yield self._glos.newEntry(word, defi)
