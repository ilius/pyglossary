# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = "DictOrgSource"
description = "DICT.org / dictfmt source file"
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

	def write(
		self,
		filename: str,
	) -> Generator[None, "BaseEntry", None]:
		remove_html_all = self._remove_html_all
		glos = self._glos
		if remove_html_all:
			glos.removeHtmlTagsAll()
		# TODO: add another bool flag to only remove html tags that are not
		# supported by GtkTextView
		yield from glos.writeTxt(
			entryFmt=":{word}:{defi}\n",
			filename=filename,
			defiEscapeFunc=replaceStringTable([
				("\r", ""),
			]),
			ext=".dtxt",
		)
