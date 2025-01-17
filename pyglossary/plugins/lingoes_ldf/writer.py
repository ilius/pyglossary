# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.compression import (
	# compressionOpen,
	stdCompressions,
)

if TYPE_CHECKING:
	from collections.abc import Generator

	from pyglossary.glossary_types import EntryType, WriterGlossaryType

__all__ = ["Writer"]


class Writer:
	compressions = stdCompressions

	_newline: str = "\n"
	_resources: bool = True

	def __init__(self, glos: WriterGlossaryType) -> None:
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
