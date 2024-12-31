# -*- coding: utf-8 -*-
from __future__ import annotations

from pyglossary.option import (
	BoolOption,
	EncodingOption,
	Option,
	StrOption,
)

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
lname = "dsl"
name = "ABBYYLingvoDSL"
description = "ABBYY Lingvo DSL (.dsl)"
extensions = (".dsl",)
extensionCreate = ".dsl"
singleFile = True
kind = "text"
wiki = "https://ru.wikipedia.org/wiki/ABBYY_Lingvo"
website = (
	"https://www.lingvo.ru/",
	"www.lingvo.ru",
)
optionsProp: dict[str, Option] = {
	"encoding": EncodingOption(),
	"audio": BoolOption(
		comment="Enable audio objects",
	),
	"example_color": StrOption(
		comment="Examples color",
	),
	"abbrev": StrOption(
		customValue=False,
		values=["", "hover"],
		comment="Load and apply abbreviation file (`_abrv.dsl`)",
	),
}

# ABBYY is a Russian company
# https://ru.wikipedia.org/wiki/ABBYY_Lingvo
# http://lingvo.helpmax.net/en/troubleshooting/dsl-compiler/compiling-a-dictionary/
# https://www.abbyy.com/news/abbyy-lingvo-80-dictionaries-to-suit-every-taste/


# {{{
# modified to work around codepoints that are not supported by `unichr`.
# http://effbot.org/zone/re-sub.htm#unescape-html
# January 15, 2003 | Fredrik Lundh


# Removes HTML or XML character references and entities from a text string.
#
# @param text The HTML (or XML) source text.
# @return The plain text, as a Unicode string, if necessary.
