# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = "DictOrgSource"
description = "DICT.org / dictfmt source file"
extensions = (".dtxt",)
singleFile = True
optionsProp = {
	"html": BoolOption(),
}

tools = [
	{
		"name": "dictfmt",
		"web": "https://linux.die.net/man/1/dictfmt",
		"platforms": ["Linux"],
		"license": "GPL",
	},
]


def write(
	glos,
	filename: str,
	html: bool = False,
) -> None:
	rplList = [
		("\r", ""),
	]
	if not html:
		rplList += [
			("<br>", "\n"),
			("<BR>", "\n"),
		]
	glos.writeTxt(
		entryFmt=":{word}:{defi}\n",
		filename=filename,
		rplList=rplList,
		ext=".dtxt",
	)
