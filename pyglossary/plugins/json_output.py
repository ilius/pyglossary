# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = "Json"
description = "JSON"
extensions = (".json",)
singleFile = True
optionsProp = {
	"encoding": EncodingOption(),
}
depends = {}


def write(
	glos: GlossaryType,
	filename: str,
	encoding: str = "utf-8",
):
	with open(filename, "w", encoding=encoding) as fp:
		for line in glos.iterJsonLines(
			transaction=False,
		):
			fp.write(line + "\n")
