# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = "Sql"
description = "SQL"
extensions = [".sql"]
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
		for line in glos.iterSqlLines(
			transaction=False,
		):
			fp.write(line + "\n")
