# -*- coding: utf-8 -*-
from __future__ import annotations

import os

from pyglossary.flags import ALWAYS, DEFAULT_YES
from pyglossary.option import (
	BoolOption,
	Option,
	StrOption,
)

from .writer import Writer

__all__ = [
	"Writer",
	"description",
	"enable",
	"extensionCreate",
	"extensions",
	"kind",
	"lname",
	"name",
	"optionsProp",
	"singleFile",
	"website",
	"wiki",
]


enable = True
lname = "stardict_merge_syns"
name = "StardictMergeSyns"
description = "StarDict (Merge Syns)"
extensions = ()
extensionCreate = "-stardict/"
singleFile = False
sortOnWrite = ALWAYS
sortKeyName = "stardict"
sortEncoding = "utf-8"

kind = "directory"
wiki = "https://en.wikipedia.org/wiki/StarDict"
website = (
	"http://huzheng.org/stardict/",
	"huzheng.org/stardict",
)
# https://github.com/huzheng001/stardict-3/blob/master/dict/doc/StarDictFileFormat
optionsProp: dict[str, Option] = {
	"large_file": BoolOption(
		comment="Use idxoffsetbits=64 bits, for large files only",
	),
	"dictzip": BoolOption(
		comment="Compress .dict file to .dict.dz",
	),
	"sametypesequence": StrOption(
		values=["", "h", "m", "x", None],
		comment="Definition format: h=html, m=plaintext, x=xdxf",
	),
	"xdxf_to_html": BoolOption(
		comment="Convert XDXF entries to HTML",
	),
	"xsl": BoolOption(
		comment="Use XSL transformation",
	),
	"unicode_errors": StrOption(
		values=[
			"strict",  # raise a UnicodeDecodeError exception
			"ignore",  # just leave the character out
			"replace",  # use U+FFFD, REPLACEMENT CHARACTER
			"backslashreplace",  # insert a \xNN escape sequence
		],
		comment="What to do with Unicode decoding errors",
	),
	"audio_icon": BoolOption(
		comment="Add glossary's audio icon",
	),
	"sqlite": BoolOption(
		comment="Use SQLite to limit memory usage."
		" Default depends on global SQLite mode.",
		allowNone=True,
	),
}

if os.getenv("PYGLOSSARY_STARDICT_NO_FORCE_SORT") == "1":
	sortOnWrite = DEFAULT_YES
