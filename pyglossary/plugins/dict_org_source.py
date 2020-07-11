# -*- coding: utf-8 -*-

from formats_common import *

enable = True
format = "DictOrgSource"
description = "DICT.org / dictfmt source file"
extensions = (".dtxt",)
singleFile = True

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
) -> None:
	glos.writeTxt(
		entryFmt=":{word}:{defi}\n",
		filename=filename,
		rplList=(
			("\\", "\\\\"),
			("\r", ""),
			("\n", "\\n"),
			("\t", "\\t"),
		),
		ext=".dtxt",
	)
