# -*- coding: utf-8 -*-
from __future__ import annotations

from pyglossary.option import (
	BoolOption,
	EncodingOption,
	Option,
)

from .reader import Reader
from .writer import Writer

__all__ = [
	"Reader",
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
lname = "stardict_textual"
name = "StardictTextual"
description = "StarDict Textual File (.xml)"
extensions = ()
extensionCreate = ".xml"
sortKeyName = "stardict"
singleFile = True
kind = "text"
wiki = ""
website = (
	"https://github.com/huzheng001/stardict-3"
	"/blob/master/dict/doc/TextualDictionaryFileFormat",
	"TextualDictionaryFileFormat",
)
optionsProp: dict[str, Option] = {
	"encoding": EncodingOption(),
	"xdxf_to_html": BoolOption(
		comment="Convert XDXF entries to HTML",
	),
}
