# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = "DictOrgSource"
description = "DICT.org dictfmt source file"
extensions = (".dtxt",)
singleFile = True
optionsProp = {
	"remove_html_all": BoolOption(),
}

tools = [
	{
		"name": "dictfmt",
		"web": "https://linux.die.net/man/1/dictfmt",
		"platforms": ["Linux"],
		"license": "GPL",
	},
]


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
		yield from self._glos.writeTxt(
			entryFmt=":{word}:{defi}\n",
			filename=self._filename,
			defiEscapeFunc=replaceStringTable([
				("\r", ""),
			]),
			ext=".dtxt",
		)
