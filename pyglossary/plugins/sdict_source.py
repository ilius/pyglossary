# -*- coding: utf-8 -*-
# Source Glossary for "Sdictionary" (http://sdict.org)
# It has extension ".sdct"

from formats_common import *

enable = True
lname = "sdict_source"
format = "SdictSource"
description = "Sdictionary Source (.sdct)"
extensions = (".sdct",)
extensionCreate = ".sdct"
singleFile = True
kind = "text"
wiki = ""
website = (
	"http://swaj.net/sdict/",
	"Sdictionary Project",
)
optionsProp = {
	"enable_info": BoolOption(comment="Enable glossary info / metedata"),
	"newline": NewlineOption(),
	"resources": BoolOption(comment="Enable resources / data files"),
}


class Writer(object):
	_enable_info: bool = True
	_newline: bool = "\n"
	_resources: bool = True

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = None

	def getInfo(self, key):
		return self._glos.getInfo(key).replace("\n", "<br>")

	def finish(self):
		self._filename = None

	def open(self, filename: str) -> None:
		self._filename = filename

	def write(self) -> "Generator[None, BaseEntry, None]":
		from pyglossary.text_writer import writeTxt
		glos = self._glos
		head = ""
		if self._enable_info:
			head = (
				"<header>\n"
				f"title = {self.getInfo('name')}\n"
				f"author = {self.getInfo('author')}\n"
				f"description = {self.getInfo('description')}\n"
				f"w_lang = {glos.sourceLangName}\n"
				f"a_lang = {glos.targetLangName}\n"
				"</header>\n#\n#\n#\n"
			)
		yield from writeTxt(
			glos,
			entryFmt="{word}___{defi}\n",
			filename=self._filename,
			writeInfo=False,
			defiEscapeFunc=replaceStringTable([
				("\n", "<BR>"),
			]),
			ext=".sdct",
			head=head,
			newline=self._newline,
			resources=self._resources,
		)
