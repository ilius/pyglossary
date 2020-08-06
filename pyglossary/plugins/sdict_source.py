# -*- coding: utf-8 -*-
# Source Glossary for "Sdictionary" (http://sdict.org)
# It has extension ".sdct"

from formats_common import *

enable = True
format = "SdictSource"
description = "Sdictionary Source (sdct)"
extensions = (".sdct",)
singleFile = True
optionsProp = {
	"writeInfo": BoolOption(),
	"newline": NewlineOption(),
	"resources": BoolOption(),
}
depends = {}

tools = [
	{
		"name": "PTkSdict",
		"web": "http://swaj.net/sdict/create-dicts.html",
		"platforms": ["Linux", "Windows", "Mac"],
		"license": "GPL",
	},
]


class Writer(object):
	_writeInfo: bool = True
	_newline: bool = "\n"
	_resources: bool = True

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos

	def getInfo(self, key):
		return self._glos.getInfo(key).replace("\n", "<br>")

	def write(
		self,
		filename,
	) -> Generator[None, "BaseEntry", None]:
		glos = self._glos
		head = ""
		if self._writeInfo:
			head = (
				"<header>\n"
				f"title = {self.getInfo('name')}\n"
				f"author = {self.getInfo('author')}\n"
				f"description = {self.getInfo('description')}\n"
				f"w_lang = {glos.sourceLangName}\n"
				f"a_lang = {glos.targetLangName}\n"
				"</header>\n#\n#\n#\n"
			)
		yield from glos.writeTxt(
			entryFmt="{word}___{defi}\n",
			filename=filename,
			writeInfo=False,
			defiEscapeFunc=replaceStringTable([
				("\n", "<BR>"),
			]),
			ext=".sdct",
			head=head,
			newline=self._newline,
			resources=self._resources,
		)
