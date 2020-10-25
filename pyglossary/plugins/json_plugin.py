# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = "Json"
description = "JSON"
extensions = (".json",)
singleFile = True
optionsProp = {
	"encoding": EncodingOption(),
	"writeInfo": BoolOption(),
	"resources": BoolOption(),
}


class Writer(object):
	_encoding: str = "utf-8"
	_writeInfo: bool = True
	_resources: bool = True

	compressions = stdCompressions

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos
		self._filename = None

	def open(self, filename: str):
		self._filename = filename

	def finish(self):
		self._filename = None

	def write(self) -> "Generator[None, BaseEntry, None]":
		from json import dumps

		glos = self._glos
		encoding = self._encoding
		writeInfo = self._writeInfo
		resources = self._resources

		ascii = encoding == "ascii"

		def escape(st):
			return dumps(st, ensure_ascii=ascii)

		yield from glos.writeTxt(
			entryFmt="\t{word}: {defi},\n",
			filename=self._filename,
			encoding=encoding,
			writeInfo=writeInfo,
			wordEscapeFunc=escape,
			defiEscapeFunc=escape,
			ext=".json",
			head="{\n",
			tail='\t"": ""\n}',
			resources=resources,
		)
