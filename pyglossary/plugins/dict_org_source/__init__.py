# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import TYPE_CHECKING

from pyglossary.option import BoolOption, Option

if TYPE_CHECKING:
	from collections.abc import Generator

	from pyglossary.glossary_types import EntryType, GlossaryType

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
lname = "dict_org_source"
name = "DictOrgSource"
description = "DICT.org dictfmt source file"
extensions = (".dtxt",)
extensionCreate = ".dtxt"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/DICT"
website = (
	"https://github.com/cheusov/dictd",
	"@cheusov/dictd",
)
optionsProp: dict[str, Option] = {
	"remove_html_all": BoolOption(comment="Remove all HTML tags"),
}


class Writer:
	_remove_html_all: bool = True

	def __init__(self, glos: GlossaryType) -> None:
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
