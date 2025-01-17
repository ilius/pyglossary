# -*- coding: utf-8 -*-

from __future__ import annotations

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
	_file_size_approx: int = 0
	_word_title: bool = False

	compressions = stdCompressions

	def __init__(self, glos: WriterGlossaryType) -> None:
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
