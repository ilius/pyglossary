# -*- coding: utf-8 -*-
from __future__ import annotations

from pyglossary.option import (
	BoolOption,
	Option,
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
lname = "xdxf_lax"
name = "XdxfLax"
description = "XDXF Lax (.xdxf)"
extensions = ()
extensionCreate = ".xdxf"
singleFile = True
kind = "text"
wiki = "https://en.wikipedia.org/wiki/XDXF"
website = (
	"https://github.com/soshial/xdxf_makedict/tree/master/format_standard",
	"XDXF standard - @soshial/xdxf_makedict",
)
optionsProp: dict[str, Option] = {
	"html": BoolOption(comment="Entries are HTML"),
	"xsl": BoolOption(
		comment="Use XSL transformation",
	),
}
