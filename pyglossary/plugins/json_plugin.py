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
depends = {}


class Writer(object):
	_encoding: str = "utf-8"
	_writeInfo: bool = True
	_resources: bool = True

	def __init__(self, glos: GlossaryType) -> None:
		self._glos = glos

	def write(
		self,
		filename: str,
	) -> Generator[None, "BaseEntry", None]:
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
			filename=filename,
			encoding=encoding,
			writeInfo=writeInfo,
			wordEscapeFunc=escape,
			defiEscapeFunc=escape,
			ext=".json",
			head="{\n",
			tail='\t"": ""\n}',
			resources=resources,
		)
