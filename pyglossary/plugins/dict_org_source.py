# -*- coding: utf-8 -*-

from formats_common import *

enable = True
lname = "dict_org_source"
format = "DictOrgSource"
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
optionsProp = {
	"remove_html_all": BoolOption(comment="Remove all HTML tags"),
}


class Writer(object):
	_remove_html_all: bool = True

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = None

	def finish(self):
		self._filename = None

	def open(self, filename: str):
		self._filename = filename
		if self._remove_html_all:
			self._glos.removeHtmlTagsAll()
		# TODO: add another bool flag to only remove html tags that are not
		# supported by GtkTextView

	def write(self) -> "Generator[None, BaseEntry, None]":
		from pyglossary.text_writer import writeTxt
		yield from writeTxt(
			self._glos,
			entryFmt=":{word}:{defi}\n",
			filename=self._filename,
			defiEscapeFunc=replaceStringTable([
				("\r", ""),
			]),
			ext=".dtxt",
		)
