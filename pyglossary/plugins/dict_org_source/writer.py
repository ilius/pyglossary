# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
	from collections.abc import Generator

	from pyglossary.glossary_types import EntryType, WriterGlossaryType

__all__ = ["Writer"]


class Writer:
	_remove_html_all: bool = True

	def __init__(self, glos: WriterGlossaryType) -> None:
		self._glos = glos
		self._filename = ""

	def finish(self) -> None:
		self._filename = ""

	def open(self, filename: str) -> None:
		self._filename = filename
		if self._remove_html_all:
			self._glos.removeHtmlTagsAll()
		# TODO: add another bool flag to only remove html tags that are not
		# supported by GtkTextView

	@staticmethod
	def _defiEscapeFunc(defi: str) -> str:
		return defi.replace("\r", "")

	def write(self) -> Generator[None, EntryType, None]:
		from pyglossary.text_writer import writeTxt

		yield from writeTxt(
			self._glos,
			entryFmt=":{word}:{defi}\n",
			filename=self._filename,
			defiEscapeFunc=self._defiEscapeFunc,
			ext=".dtxt",
		)
