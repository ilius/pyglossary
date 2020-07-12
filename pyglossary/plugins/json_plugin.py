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

def write(
	glos: GlossaryType,
	filename: str,
	encoding: str = "utf-8",
	writeInfo: bool = True,
	resources: bool = True,
) -> bool:
	from json import dumps
	return glos.writeTxt(
		entryFmt="\t{word}: {defi},\n",
		filename=filename,
		encoding=encoding,
		writeInfo=writeInfo,
		wordEscapeFunc=dumps,
		defiEscapeFunc=dumps,
		ext=".json",
		head="{\n",
		tail='\t"": ""\n}',
		resources=resources,
	)
