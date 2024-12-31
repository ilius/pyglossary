# -*- coding: utf-8 -*-
from __future__ import annotations

from pyglossary.option import BoolOption, Option

from .reader import Reader

__all__ = [
	"Reader",
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
lname = "appledict_bin"
name = "AppleDictBin"
description = "AppleDict Binary"
extensions = (".dictionary", ".data")
extensionCreate = ""
singleFile = True
kind = "binary"
wiki = ""
website = (
	"https://support.apple.com/en-gu/guide/dictionary/welcome/mac",
	"Dictionary User Guide for Mac",
)
optionsProp: dict[str, Option] = {
	"html": BoolOption(comment="Entries are HTML"),
	"html_full": BoolOption(
		comment="Turn every entry's definition into an HTML document",
	),
}
